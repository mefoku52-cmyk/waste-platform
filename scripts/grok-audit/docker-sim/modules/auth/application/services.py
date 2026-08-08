import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.application.dto import AuthTokenPairDTO
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.infrastructure.security.jwt_service import JwtService
from app.shared.infrastructure.security.jwt_exceptions import (
    TokenExpiredError,
    TokenFamilyRevokedError,
    TokenRevokedError,
    InvalidTokenError,
)
from app.shared.domain.ports.clock import Clock
from app.shared.domain.exceptions import UnauthorizedDomainError

logger = logging.getLogger(__name__)


class LoginService:
    def __init__(self, jwt_service: JwtService, user_repo: SqlAlchemyUserRepository):
        self.jwt_service = jwt_service
        self.user_repo = user_repo

    async def execute(self, email: str, password: str) -> AuthTokenPairDTO:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = await self.user_repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.password_hash):
            raise UnauthorizedDomainError("Invalid credentials")
        
        subject = str(user.id)
        family_id = str(uuid4())
        
        access_token, access_expires_at = await self.jwt_service.issue_access_token(subject=subject)
        refresh_token, refresh_jti, refresh_expires_at = await self.jwt_service.issue_refresh_token(
            subject=subject,
            family_id=family_id,
        )
        
        expires_in = int((access_expires_at - datetime.now(timezone.utc)).total_seconds())
        
        return AuthTokenPairDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=expires_in,
        )


class RefreshTokenService:
    def __init__(self, jwt_service: JwtService, clock: Clock):
        self.jwt_service = jwt_service
        self.clock = clock

    async def execute(self, refresh_token: str) -> AuthTokenPairDTO:
        try:
            payload = await self.jwt_service.decode_and_validate(refresh_token, expected_type="refresh")
        except TokenFamilyRevokedError as e:
            logger.warning(f"Replay attack detected: {e}")
            raise UnauthorizedDomainError("Session invalidated due to security concern")
        
        sub = payload.get("sub")
        family_id = payload.get("family_id")
        old_jti = payload.get("jti")
        old_exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
        
        if await self.jwt_service.revocation_store.is_family_revoked(family_id):
            raise UnauthorizedDomainError("Session has been revoked")
        
        await self.jwt_service.revoke_refresh_token(old_jti, family_id, old_exp)
        
        access_token, access_expires_at = await self.jwt_service.issue_access_token(subject=sub)
        new_refresh_token, new_jti, refresh_expires_at = await self.jwt_service.issue_refresh_token(
            subject=sub, family_id=family_id
        )
        
        expires_in = int((access_expires_at - datetime.now(timezone.utc)).total_seconds())
        
        return AuthTokenPairDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=expires_in,
        )


class GetCurrentAuthContextService:
    def __init__(self, jwt_service: JwtService):
        self.jwt_service = jwt_service

    async def execute(self, access_token: str) -> dict:
        try:
            payload = await self.jwt_service.decode_and_validate(access_token, expected_type="access")
        except TokenExpiredError:
            raise UnauthorizedDomainError("Token has expired")
        except TokenRevokedError:
            raise UnauthorizedDomainError("Token has been revoked")
        except InvalidTokenError as e:
            raise UnauthorizedDomainError(f"Invalid token: {e.message}")
        
        return {"sub": payload.get("sub"), "roles": payload.get("roles", [])}


class LogoutService:
    def __init__(self, jwt_service: JwtService):
        self.jwt_service = jwt_service

    async def execute(self, refresh_token: str | None = None) -> None:
        if refresh_token:
            try:
                refresh_payload = await self.jwt_service.decode_and_validate(refresh_token, expected_type="refresh")
                refresh_jti = refresh_payload.get("jti")
                refresh_family = refresh_payload.get("family_id")
                refresh_exp = datetime.fromtimestamp(refresh_payload.get("exp"), tz=timezone.utc)
                await self.jwt_service.revoke_refresh_token(refresh_jti, refresh_family, refresh_exp)
            except Exception as e:
                logger.debug(f"Could not revoke refresh token: {e}")
        
        logger.info("User logged out successfully")
