from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.domain.entities import CompanyMembership


def to_membership_dto(entity: CompanyMembership) -> CompanyMembershipDTO:
    return CompanyMembershipDTO(
        id=entity.id,
        status=entity.status.value,
        company_id=entity.company_id,
        user_id=entity.user_id,
        membership_role=entity.membership_role.value,
        is_primary_contact=entity.is_primary_contact,
        invited_at=entity.invited_at,
        joined_at=entity.joined_at,
        left_at=entity.left_at,
        created_at=entity.created_at,
        created_by_user_id=entity.created_by_user_id,
        updated_at=entity.updated_at,
        updated_by_user_id=entity.updated_by_user_id,
    )
