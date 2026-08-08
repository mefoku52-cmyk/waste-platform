from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.services import (
    LoginService,
    RefreshTokenService,
    GetCurrentAuthContextService,
    LogoutService,
)
from app.shared.infrastructure.security.jwt_service import JwtService
from app.shared.infrastructure.security.jwt_revocation_store import get_revocation_store
from app.shared.infrastructure.db.session import get_db_session
from app.shared.domain.ports.clock import SystemClock
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository


def get_jwt_service() -> JwtService:
    revocation_store = get_revocation_store()
    return JwtService(revocation_store=revocation_store)


def get_auth_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> GetCurrentAuthContextService:
    return GetCurrentAuthContextService(jwt_service=jwt_service)


def get_login_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginService:
    user_repo = SqlAlchemyUserRepository(session=session)
    return LoginService(jwt_service=jwt_service, user_repo=user_repo)


def get_refresh_token_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> RefreshTokenService:
    clock = SystemClock()
    return RefreshTokenService(jwt_service=jwt_service, clock=clock)


def get_logout_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> LogoutService:
    return LogoutService(jwt_service=jwt_service)


def get_refresh_token_service_alias():
    return get_refresh_token_service
