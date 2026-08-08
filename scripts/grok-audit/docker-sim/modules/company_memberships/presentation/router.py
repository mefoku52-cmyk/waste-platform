from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.company_memberships.presentation.dependencies import (
    get_create_membership_service,
    get_list_memberships_service,
    get_transition_membership_status_service,
    get_update_membership_service,
)
from app.modules.company_memberships.presentation.mappers import to_membership_data
from app.modules.company_memberships.presentation.schemas import (
    CompanyMembershipCreateRequest,
    CompanyMembershipResponse,
    CompanyMembershipStatusTransitionRequest,
    CompanyMembershipUpdateRequest,
)
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(tags=["company-memberships"])


@router.get("/companies/{company_id}/memberships")
async def list_company_memberships(
    company_id: UUID,
    status: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_memberships_service),
):
    items = await service.execute(company_id=company_id, status=status)
    return {
        "items": [to_membership_data(item).model_dump() for item in items],
        "meta": {"page": 1, "pageSize": len(items), "total": len(items)},
    }


@router.post("/companies/{company_id}/memberships", response_model=CompanyMembershipResponse, status_code=201)
async def create_company_membership(
    company_id: UUID,
    payload: CompanyMembershipCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_membership_service),
):
    dto = await service.execute(
        company_id=company_id,
        user_id=payload.userId,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch("/company-memberships/{membership_id}", response_model=CompanyMembershipResponse)
async def update_company_membership(
    membership_id: UUID,
    payload: CompanyMembershipUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_membership_service),
):
    dto = await service.execute(
        membership_id=membership_id,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch("/company-memberships/{membership_id}/status", response_model=CompanyMembershipResponse)
async def transition_company_membership_status(
    membership_id: UUID,
    payload: CompanyMembershipStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_membership_status_service),
):
    dto = await service.execute(
        membership_id=membership_id,
        to_status=payload.toStatus,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))
