from uuid import UUID

from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel


def to_domain(model: CompanyMembershipModel) -> CompanyMembership:
    return CompanyMembership(
        id=UUID(model.id),
        status=CompanyMembershipStatus(model.status),
        company_id=UUID(model.company_id),
        user_id=UUID(model.user_id),
        membership_role=CompanyMembershipRole(model.membership_role),
        is_primary_contact=model.is_primary_contact,
        invited_at=model.invited_at,
        joined_at=model.joined_at,
        left_at=model.left_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: CompanyMembership) -> CompanyMembershipModel:
    return CompanyMembershipModel(
        id=str(entity.id),
        status=entity.status.value,
        company_id=str(entity.company_id),
        user_id=str(entity.user_id),
        membership_role=entity.membership_role.value,
        is_primary_contact=entity.is_primary_contact,
        invited_at=entity.invited_at,
        joined_at=entity.joined_at,
        left_at=entity.left_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )
