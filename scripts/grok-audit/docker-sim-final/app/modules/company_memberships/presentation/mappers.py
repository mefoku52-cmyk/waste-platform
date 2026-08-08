from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.presentation.schemas import CompanyMembershipData


def to_membership_data(dto: CompanyMembershipDTO) -> CompanyMembershipData:
    return CompanyMembershipData(
        id=dto.id,
        status=dto.status,
        companyId=dto.company_id,
        userId=dto.user_id,
        membershipRole=dto.membership_role,
        isPrimaryContact=dto.is_primary_contact,
        invitedAt=dto.invited_at,
        joinedAt=dto.joined_at,
        leftAt=dto.left_at,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )
