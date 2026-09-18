from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.company_memberships.presentation.dependencies import (
    get_create_membership_service,
    get_list_memberships_service,
    get_membership_repo,
    get_transition_membership_status_service,
    get_update_membership_service,
)
from app.modules.company_memberships.presentation.mappers import to_membership_data
from app.modules.company_memberships.presentation.schemas import (
    CompanyMembershipCreateRequest,
    CompanyMembershipResponse,
    CompanyMembershipStatusTransitionRequest,
    CompanyMembershipUpdateRequest,
    PaginatedCompanyMembershipsResponse,
    PaginationMeta,
)
from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    require_company_admin,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(tags=["company-memberships"])


async def _membership_company_id(repo, membership_id: UUID) -> UUID:
    """Najdi company_id clenstva, aby sa dalo overit opravnenie voci firme."""
    membership = await repo.get_by_id(membership_id)
    if membership is None:
        raise NotFoundDomainError("Company membership not found")
    return membership.company_id


@router.get(
    "/companies/{company_id}/memberships",
    response_model=PaginatedCompanyMembershipsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_company_memberships(
    company_id: UUID,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=100, ge=1, le=100),
    current_user=Depends(require_current_user),
    service=Depends(get_list_memberships_service),
):
    # Zoznam clenov firmy vidi len clen danej firmy (alebo platform admin).
    require_company_member(current_user, company_id, action="access")

    items = await service.execute(company_id=company_id, status=status)
    start = (page - 1) * pageSize
    slice_items = items[start : start + pageSize]
    return PaginatedCompanyMembershipsResponse(
        items=[to_membership_data(item) for item in slice_items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=len(items)),
    )


@router.post(
    "/companies/{company_id}/memberships",
    response_model=CompanyMembershipResponse,
    status_code=201,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_company_membership(
    company_id: UUID,
    payload: CompanyMembershipCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_membership_service),
):
    # Pridavat clenov smie len tenant admin danej firmy (alebo platform admin).
    require_company_admin(current_user, company_id, action="manage members of")

    dto = await service.execute(
        company_id=company_id,
        user_id=payload.userId,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch(
    "/company-memberships/{membership_id}",
    response_model=CompanyMembershipResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_company_membership(
    membership_id: UUID,
    payload: CompanyMembershipUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_membership_service),
    repo=Depends(get_membership_repo),
):
    company_id = await _membership_company_id(repo, membership_id)
    require_company_admin(current_user, company_id, action="manage members of")

    dto = await service.execute(
        membership_id=membership_id,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch(
    "/company-memberships/{membership_id}/status",
    response_model=CompanyMembershipResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def transition_company_membership_status(
    membership_id: UUID,
    payload: CompanyMembershipStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_membership_status_service),
    repo=Depends(get_membership_repo),
):
    company_id = await _membership_company_id(repo, membership_id)
    require_company_admin(current_user, company_id, action="manage members of")

    dto = await service.execute(
        membership_id=membership_id,
        to_status=payload.toStatus,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))
