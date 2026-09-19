"""Email verification via Redis token + optional SMTP.

Flow:
1. Po registracii sa vytvori user so status='pending_verification'.
2. request_verification(email) vygeneruje token, ulozi do Redis (TTL 24h), posle mail.
3. Pouzivatel klikne na link vo formate {FRONTEND_URL}/verify-email?token=...
4. verify(token) overi token, aktivuje usera (status='active').
5. Token sa spotrebuje (pop) a je jednorazovy.
"""

from __future__ import annotations

import hashlib
import logging
import secrets

from app.core.config import settings
from app.modules.users.domain.enums import UserStatus
from app.modules.users.domain.repositories import UserRepository
from app.shared.infrastructure.email.sender import send_email

logger = logging.getLogger(__name__)

VERIFY_PREFIX = "emailverify:"
VERIFY_TTL_SECONDS = 60 * 60 * 24  # 24 hodin


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EmailVerificationService:
    _mem: dict = {}

    def __init__(self, user_repo: UserRepository, redis_client=None):
        self.user_repo = user_repo
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
        from app.shared.domain.exceptions import ValidationDomainError

        key = VERIFY_PREFIX + _token_digest(token)
        r = self._get_redis()
        if r is not None:
            r.set(key, user_id, ex=VERIFY_TTL_SECONDS)
            return

        if settings.is_development:
            logger.warning("Email verification using in-memory fallback storage")
            EmailVerificationService._mem[key] = user_id
            return

        logger.error("Email verification unavailable: Redis is not reachable")
        raise ValidationDomainError("Overenie e-mailu je dočasne nedostupné. Skúste to neskôr.")

    def _pop_token(self, token: str) -> str | None:
        key = VERIFY_PREFIX + _token_digest(token)
        r = self._get_redis()
        if r is not None:
            uid = r.get(key)
            if uid:
                r.delete(key)
            return uid

        if settings.is_development:
            return EmailVerificationService._mem.pop(key, None)

        return None

    async def request_verification(self, email: str) -> dict:
        """Posle verifikacny mail (alebo ticho neuspeje, ak user neexistuje)."""
        email_n = email.lower().strip()
        user = await self.user_repo.get_by_email(email_n)
        result = {
            "ok": True,
            "message": "Ak účet existuje a nie je overený, poslali sme verifikačný e-mail.",
        }
        if user is None:
            return result

        # Ak je uz overeny (active), nic neposielame, ale vraciame rovnaku odpoved
        if user.status != UserStatus.PENDING_VERIFICATION:
            return result

        token = secrets.token_urlsafe(32)
        self._store_token(token, str(user.id))

        import os

        base = (
            os.environ.get("FRONTEND_URL")
            or getattr(settings, "FRONTEND_URL", "")
            or "https://waste-platform-web.onrender.com"
        ).rstrip("/")
        if "127.0.0.1" in base or "localhost" in base:
            base = "https://waste-platform-web.onrender.com"

        nl = chr(10)
        body = (
            "Vitajte v CMEP"
            + nl
            + nl
            + "Pre dokončenie registrácie overte svoj e-mail kliknutím na odkaz nižšie."
            + nl
            + nl
            + f"Overiť e-mail: {base}/verify-email?token={token}"
            + nl
            + nl
            + "Odkaz je platný 24 hodín."
            + nl
            + nl
            + "Ak ste sa neregistrovali, ignorujte tento e-mail."
            + nl
        )
        sent = send_email(to=email_n, subject="CMEP – overenie e-mailu", body=body)
        result["emailSent"] = bool(sent)
        if settings.is_development:
            result["verifyToken"] = token
        return result

    async def verify(self, token: str) -> dict:
        """Overi token a aktivuje usera. Token je jednorazovy."""
        from uuid import UUID

        from app.shared.domain.exceptions import ValidationDomainError

        if not token or len(token) < 10:
            raise ValidationDomainError("Neplatný alebo chýbajúci token.")

        user_id = self._pop_token(token)
        if not user_id:
            raise ValidationDomainError("Token je neplatný alebo expirovaný.")

        user = await self.user_repo.get_by_id(UUID(str(user_id)))
        if user is None:
            raise ValidationDomainError("Účet neexistuje.")

        if user.status == UserStatus.ACTIVE:
            return {"ok": True, "message": "E-mail už bol overený."}

        if user.status != UserStatus.PENDING_VERIFICATION:
            raise ValidationDomainError(f"Účet nie je možné overiť (stav: {user.status.value}).")

        user.transition_status(UserStatus.ACTIVE)
        await self.user_repo.update(user)
        return {"ok": True, "message": "E-mail bol úspešne overený."}
