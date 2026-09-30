from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt

from app.core.config import settings
from app.shared.infrastructure.security.jwt_exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenFamilyRevokedError,
    TokenRevokedError,
    TokenTypeMismatchError,
    TokenUserRevokedError,
)
from app.shared.infrastructure.security.jwt_revocation_store import (
    TokenRevocationStore,
    get_revocation_store,
)

_jwt = settings.jwt
assert _jwt is not None, "JWT settings are not configured"
JWT_SECRET = _jwt.secret_key
JWT_ALGORITHM = _jwt.algorithm
ACCESS_TOKEN_TTL_MINUTES = _jwt.access_token_expire_minutes
REFRESH_TOKEN_TTL_DAYS = int(str(_jwt.refresh_token_expire_days))


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
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "jti": jti,
            "iat": issued_at,
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), expires_at

    async def issue_refresh_token(
        self, subject: str, family_id: str, extra_claims: dict[str, Any] | None = None
    ) -> tuple[str, str, datetime]:
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(days=REFRESH_TOKEN_TTL_DAYS)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "refresh",
            "jti": jti,
            "family_id": family_id,
            "iat": issued_at,
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti, expires_at

    async def issue_2fa_token(self, subject: str) -> tuple[str, datetime]:
        """Kratkodoby token, ktory opravnuje dokoncit 2FA login. 5 minut."""
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=5)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "2fa",
            "jti": jti,
            "iat": issued_at,
            "exp": expires_at,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), expires_at

    async def decode_2fa_token(self, token: str) -> dict[str, Any]:
        """Overi 2FA token (typ='2fa') a vrati payload."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("2FA token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid 2FA token: {e!s}")
        if payload.get("type") != "2fa":
            raise TokenTypeMismatchError("Expected 2fa token")
        return payload

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
            raise InvalidTokenError(f"Invalid token: {e!s}")

        token_type = payload.get("type")
        if token_type != expected_type:
            raise TokenTypeMismatchError(f"Expected {expected_type} token, got {token_type}")

        sub = payload.get("sub")
        iat_raw = payload.get("iat")
        if sub and iat_raw is not None:
            token_issued_at = datetime.fromtimestamp(iat_raw, tz=UTC)
            revoked_after = await self.revocation_store.get_user_tokens_revoked_after(sub)
            if revoked_after is not None and token_issued_at <= revoked_after:
                raise TokenUserRevokedError("All existing user sessions have been revoked")

        if expected_type == "access":
            jti = payload.get("jti")
            if jti and await self.revocation_store.is_access_token_revoked(jti):
                raise TokenRevokedError("Access token has been revoked")

        if expected_type == "refresh":
            family_id = payload.get("family_id")
            if family_id and await self.revocation_store.is_family_revoked(family_id):
                raise TokenFamilyRevokedError("Token family revoked - possible replay attack")

        return payload

    async def revoke_access_token(self, jti: str, exp: datetime) -> None:
        await self.revocation_store.revoke_access_token(jti, exp)

    async def revoke_refresh_token(self, jti: str, family_id: str, exp: datetime) -> None:
        await self.revocation_store.revoke_refresh_token(jti, family_id, exp)

    async def revoke_all_user_tokens(self, subject: str, cutoff: datetime | None = None) -> None:
        await self.revocation_store.revoke_user_tokens_after(
            subject,
            cutoff or datetime.now(UTC),
        )

    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
