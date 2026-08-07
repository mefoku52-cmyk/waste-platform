import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4
import jwt
from app.core.config import settings
from app.shared.infrastructure.security.jwt_revocation_store import get_revocation_store, TokenRevocationStore
from app.shared.infrastructure.security.jwt_exceptions import (
    TokenExpiredError,
    TokenRevokedError,
    TokenFamilyRevokedError,
    InvalidTokenError,
    TokenTypeMismatchError,
)

JWT_SECRET = settings.jwt.secret_key
JWT_ALGORITHM = settings.jwt.algorithm
ACCESS_TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15"))
REFRESH_TOKEN_TTL_DAYS = int(str(settings.jwt.refresh_token_expire_days))


class JwtService:
    def __init__(self, revocation_store: TokenRevocationStore | None = None):
        self._revocation_store = revocation_store
        self._owns_store = revocation_store is None
    
    @property
    def revocation_store(self) -> TokenRevocationStore:
        if self._revocation_store is None:
            self._revocation_store = get_revocation_store()
        return self._revocation_store
    
    async def issue_access_token(
        self, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "jti": jti,
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), expires_at
    
    async def issue_refresh_token(
        self, subject: str, family_id: str, extra_claims: dict[str, Any] | None = None
    ) -> tuple[str, str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_TTL_DAYS)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "refresh",
            "jti": jti,
            "family_id": family_id,
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti, expires_at
    
    async def decode_and_validate(
        self, token: str, expected_type: str = "access"
    ) -> dict[str, Any]:
        """
        Decode and validate token with full security checks.
        - Verifies signature
        - Checks expiry
        - Checks revocation list
        - Validates token type
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        
        token_type = payload.get("type")
        if token_type != expected_type:
            raise TokenTypeMismatchError(f"Expected {expected_type} token, got {token_type}")
        
        if expected_type == "access":
            jti = payload.get("jti")
            if await self.revocation_store.is_access_token_revoked(jti):
                raise TokenRevokedError("Access token has been revoked")
        
        if expected_type == "refresh":
            family_id = payload.get("family_id")
            if await self.revocation_store.is_family_revoked(family_id):
                raise TokenFamilyRevokedError("Token family revoked - possible replay attack")
        
        return payload
    
    async def revoke_access_token(self, jti: str, exp: datetime) -> None:
        await self.revocation_store.revoke_access_token(jti, exp)
    
    async def revoke_refresh_token(self, jti: str, family_id: str, exp: datetime) -> None:
        await self.revocation_store.revoke_refresh_token(jti, family_id, exp)
    
    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
