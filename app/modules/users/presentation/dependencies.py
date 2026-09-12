from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.application.services import (
    CreateUserService,
    GetUserService,
    ListUsersService,
    TransitionUserStatusService,
    UpdateUserService,
)
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_create_user_service(
    repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> CreateUserService:
    return CreateUserService(repo=repo, uuid_generator=UuidGenerator(), clock=Clock())


def get_get_user_service(
    repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> GetUserService:
    return GetUserService(repo=repo)


def get_list_users_service(
    repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> ListUsersService:
    return ListUsersService(repo=repo)


def get_update_user_service(
    repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> UpdateUserService:
    return UpdateUserService(repo=repo, clock=Clock())


def get_transition_user_status_service(
    repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> TransitionUserStatusService:
    return TransitionUserStatusService(repo=repo, clock=Clock())


def get_password_service() -> PasswordService:
    return PasswordService()
