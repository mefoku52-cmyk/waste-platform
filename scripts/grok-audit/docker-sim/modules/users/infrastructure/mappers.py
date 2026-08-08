from uuid import UUID

from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.modules.users.infrastructure.models import UserModel


def to_domain(model: UserModel) -> User:
    return User(
        id=UUID(model.id),
        status=UserStatus(model.status),
        email=model.email,
        password_hash=model.password_hash,
        first_name=model.first_name,
        last_name=model.last_name,
        display_name=model.display_name,
        phone=model.phone,
        locale=model.locale,
        timezone=model.timezone,
        last_login_at=model.last_login_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: User) -> UserModel:
    return UserModel(
        id=str(entity.id),
        status=entity.status.value,
        email=entity.email,
        password_hash=entity.password_hash,
        first_name=entity.first_name,
        last_name=entity.last_name,
        display_name=entity.display_name,
        phone=entity.phone,
        locale=entity.locale,
        timezone=entity.timezone,
        last_login_at=entity.last_login_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )
