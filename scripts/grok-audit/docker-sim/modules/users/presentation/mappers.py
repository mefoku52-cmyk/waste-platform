from app.modules.users.application.dto import UserDTO
from app.modules.users.presentation.schemas import UserData


def to_user_data(dto: UserDTO) -> UserData:
    return UserData(
        id=dto.id,
        status=dto.status,
        email=dto.email,
        firstName=dto.first_name,
        lastName=dto.last_name,
        displayName=dto.display_name,
        phone=dto.phone,
        locale=dto.locale,
        timezone=dto.timezone,
        lastLoginAt=dto.last_login_at,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )
