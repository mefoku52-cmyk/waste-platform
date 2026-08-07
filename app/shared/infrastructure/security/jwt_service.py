import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from app.core.config import settings

JWT_SECRET = settings.jwt.secret_key
JWT_ALGORITHM = settings.jwt.algorithm
ACCESS_TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15"))
REFRESH_TOKEN_TTL_DAYS = int(str(settings.jwt.refresh_token_expire_days))


class JwtService:
    def issue_access_token(self, subject: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "jti": str(uuid4()),
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), expires_at

    def issue_refresh_token(self, subject: str, family_id: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, str, datetime]:
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

    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
