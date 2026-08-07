from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.services import (
    GetCurrentAuthContextService,
    LoginService,
    LogoutService,
    RefreshTokenService,
)
from app.modules.auth.infrastructure.repositories import SqlAlchemyRefreshSessionRepository
from app.modules.company_memberships.infrastructure.repositories import SqlAlchemyCompanyMembershipRepository
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session
from app.shared.infrastructure.security.jwt_service import JwtService


def get_refresh_session_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyRefreshSessionRepository:
    return SqlAlchemyRefreshSessionRepository(session)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> GetCurrentAuthContextService:
    user_repo = SqlAlchemyUserRepository(session)
    membership_repo = SqlAlchemyCompanyMembershipRepository(session)
    return GetCurrentAuthContextService(
        user_repo=user_repo,
        membership_repo=membership_repo,
        jwt_service=JwtService(),
    )


def get_login_service(
    session: AsyncSession = Depends(get_db_session),
) -> LoginService:
    return LoginService(
        user_repo=SqlAlchemyUserRepository(session),
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        membership_repo=SqlAlchemyCompanyMembershipRepository(session),
        password_service=PasswordService(),
        jwt_service=JwtService(),
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )


def get_refresh_token_service(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshTokenService:
    return RefreshTokenService(
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        jwt_service=JwtService(),
        clock=Clock(),
    )


def get_logout_service(
    session: AsyncSession = Depends(get_db_session),
) -> LogoutService:
    return LogoutService(
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        jwt_service=JwtService(),
        clock=Clock(),
    )
