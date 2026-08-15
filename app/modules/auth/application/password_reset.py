"""Password reset via Redis token + optional SMTP."""

from __future__ import annotations

import logging
import secrets
from uuid import UUID

from app.core.config import settings
from app.modules.users.domain.repositories import UserRepository
from app.shared.application.passwords import PasswordService
from app.shared.infrastructure.email.sender import send_email

logger = logging.getLogger(__name__)

RESET_PREFIX = "pwdreset:"
RESET_TTL_SECONDS = 60 * 30


class PasswordResetService:
    _mem: dict = {}

    def __init__(self, user_repo: UserRepository, password_service: PasswordService, redis_client=None):
        self.user_repo = user_repo
        self.password_service = password_service
        self.redis = redis_client

    def _get_redis(self):
        if self.redis is not None:
            return self.redis
        try:
            import redis
            host = getattr(settings.redis, "host", "localhost")
            port = getattr(settings.redis, "port", 6379)
            url = getattr(settings.redis, "url", None) or f"redis://{host}:{port}/0"
            self.redis = redis.from_url(url, decode_responses=True)
            self.redis.ping()
            return self.redis
        except Exception:
            self.redis = None
            return None

    def _store_token(self, token: str, user_id: str) -> None:
        key = RESET_PREFIX + token
        r = self._get_redis()
        if r is not None:
            r.setex(key, RESET_TTL_SECONDS, user_id)
        else:
            PasswordResetService._mem[key] = user_id

    def _pop_token(self, token: str) -> str | None:
        key = RESET_PREFIX + token
        r = self._get_redis()
        if r is not None:
            uid = r.get(key)
            if uid:
                r.delete(key)
            return uid
        return PasswordResetService._mem.pop(key, None)

    async def request_reset(self, email: str) -> dict:
        email_n = email.lower().strip()
        user = await self.user_repo.get_by_email(email_n)
        result = {"ok": True, "message": "Ak účet existuje, poslali sme inštrukcie na e-mail."}
        if user is None:
            return result
        token = secrets.token_urlsafe(32)
        self._store_token(token, str(user.id))
        body = (
            "Obnova hesla CMEP\n\n"
            f"Token (platný 30 min): {token}\n\n"
            f"Link: http://localhost:3001/reset-password?token={token}\n"
        )
        sent = send_email(to=email_n, subject="CMEP – obnova hesla", body=body)
        if settings.is_development or not sent:
            result["resetToken"] = token
            result["emailSent"] = bool(sent)
        else:
            result["emailSent"] = True
        return result

    async def reset_password(self, token: str, new_password: str) -> None:
        from app.shared.domain.exceptions import ValidationDomainError, NotFoundDomainError

        if not token or len(new_password) < 8:
            raise ValidationDomainError("Neplatný token alebo heslo (min. 8 znakov).")
        user_id = self._pop_token(token)
        if not user_id:
            raise ValidationDomainError("Token je neplatný alebo expirovaný.")
        user = await self.user_repo.get_by_id(UUID(str(user_id)))
        if user is None:
            raise NotFoundDomainError("User not found")
        user.password_hash = self.password_service.hash_password(new_password)
        await self.user_repo.update(user)
