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
    current_user_id,
    is_platform_admin,
    membership_role_in_company,
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


def _require_owner_or_platform_admin(current_user, company_id, *, action: str = "manage roles"):
    """Zmenu roly smie vykonat IBA owner firmy alebo platform admin.

    Tenant rola `admin` NIE JE dostatocna na zmenu roly — inak by si
    admin mohol povysit seba alebo kolegu na ownera (privilege escalation).
    """
    from app.shared.domain.exceptions import ForbiddenDomainError

    if is_platform_admin(current_user):
        return
    role = membership_role_in_company(current_user, company_id)
    if role != "owner":
        raise ForbiddenDomainError(f"Only a company owner or platform admin may {action}.")


def _role_value(role) -> str:
    """Enum alebo str -> lowercase string."""
    if hasattr(role, "value"):
        return str(role.value).lower()
    return str(role).lower()


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
    from app.shared.domain.exceptions import ForbiddenDomainError

    company_id = await _membership_company_id(repo, membership_id)
    require_company_admin(current_user, company_id, action="manage members of")

    # Rola sa meni len ak klient poslal membershipRole.
    if payload.membershipRole is not None:
        _require_owner_or_platform_admin(
            current_user,
            company_id,
            action="change membership roles",
        )

        target = await repo.get_by_id(membership_id)
        if target is None:
            raise NotFoundDomainError("Company membership not found")

        actor_id = current_user_id(current_user)
        target_user_id = str(getattr(target, "user_id", "") or "")

        # 1. Self-role-change zakazane (self-promotion/demotion).
        if actor_id is not None and target_user_id == str(actor_id):
            raise ForbiddenDomainError(
                "You cannot change your own membership role. Ask another owner or a platform admin."
            )

        # 2. Last-owner protection: ak sa aktualny owner degraduje na non-owner,
        #    musi ostat aspon jeden dalsi owner vo firme.
        current_role = _role_value(getattr(target, "membership_role", ""))
        new_role = _role_value(payload.membershipRole)
        if current_role == "owner" and new_role != "owner":
            all_members = await repo.list_by_company_id(company_id)
            owners = [
                m
                for m in all_members
                if _role_value(getattr(m, "membership_role", "")) == "owner"
                and str(getattr(m, "id", "")) != str(membership_id)
            ]
            if not owners:
                raise ForbiddenDomainError("Cannot demote the last owner of the company.")

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
