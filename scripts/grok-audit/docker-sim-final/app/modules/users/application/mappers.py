from app.modules.users.application.dto import UserDTO
from app.modules.users.domain.entities import User


def to_user_dto(user: User) -> UserDTO:
    return UserDTO(
        id=user.id,
        status=user.status.value,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        phone=user.phone,
        locale=user.locale,
        timezone=user.timezone,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        created_by_user_id=user.created_by_user_id,
        updated_at=user.updated_at,
        updated_by_user_id=user.updated_by_user_id,
    )
