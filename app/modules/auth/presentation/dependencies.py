from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.email_verification import EmailVerificationService
from app.modules.auth.application.password_reset import PasswordResetService
from app.modules.auth.application.services import (
    GetCurrentAuthContextService,
    LoginService,
    LogoutService,
    RefreshTokenService,
)
from app.modules.auth.application.two_factor import TwoFactorService
from app.modules.company_memberships.infrastructure.repositories import (
    SqlAlchemyCompanyMembershipRepository,
)
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.application.passwords import PasswordService
from app.shared.domain.ports.clock import SystemClock
from app.shared.infrastructure.db.session import get_db_session
from app.shared.infrastructure.security.jwt_revocation_store import get_revocation_store
from app.shared.infrastructure.security.jwt_service import JwtService


def get_jwt_service() -> JwtService:
    revocation_store = get_revocation_store()
    return JwtService(revocation_store=revocation_store)


def get_two_factor_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TwoFactorService:
    return TwoFactorService(session=session)


def get_password_service() -> PasswordService:
    return PasswordService()


def get_auth_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GetCurrentAuthContextService:
    user_repo = SqlAlchemyUserRepository(session=session)
    membership_repo = SqlAlchemyCompanyMembershipRepository(session=session)
    return GetCurrentAuthContextService(
        jwt_service=jwt_service,
        user_repo=user_repo,
        membership_repo=membership_repo,
    )


def get_login_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    two_factor_service: Annotated[TwoFactorService, Depends(get_two_factor_service)],
) -> LoginService:
    user_repo = SqlAlchemyUserRepository(session=session)
    return LoginService(
        jwt_service=jwt_service,
        user_repo=user_repo,
        password_service=password_service,
        two_factor_service=two_factor_service,
    )


def get_password_reset_service(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    password_service: Annotated[PasswordService, Depends(get_password_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PasswordResetService:
    user_repo = SqlAlchemyUserRepository(session=session)
    return PasswordResetService(
        user_repo=user_repo,
        password_service=password_service,
        jwt_service=jwt_service,
    )


def get_email_verification_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmailVerificationService:
    user_repo = SqlAlchemyUserRepository(session=session)
    return EmailVerificationService(user_repo=user_repo)


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
