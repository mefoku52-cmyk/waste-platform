"""Minting kratkych streamovacich tokenov pre CMEP Streaming.

Format je ROVNAKY ako v streamingovej sluzbe (cmep-streaming/backend/src/auth.js):
    payload = base64url(JSON claims)
    token   = payload + "." + base64url(HMAC-SHA256(payload, secret))

Claims:
    sub        — UUID pouzivatela platformy (identita, NIKDY z klienta)
    companyId  — firma ucastnika (tenancy)
    insp       — UUID obhliadky — viaze token na KONKRETNU obhliadku
    offerId    — v http mode totozny s `insp` (ID obhliadky == room.offerId == parameter
                 offer= v publishUrl; pouziva sa aj pri ingeste eventov zo streamingu)
    listingId  — UUID ponuky, z ktorej obhliadka vznikla (dohladatelnost)
    role       — 'publisher' | 'viewer'
    rec        — 1 ak majitel vyslovil suhlas s nahranim, inak 0
    iat / exp  — sekundy od epochy

Overenie vykonava VYLUCNE streaming (verifyLocalSessionToken) — token sa
generuje iba tu (server-side), TTL je kratky, revokacia je riesena cez stav
obhliadky na platforme (HttpAdapter verify => fail-closed).
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from uuid import UUID

from app.core.config import settings
from app.modules.inspections.application.dto import StreamingToken
from app.shared.domain.exceptions import ValidationDomainError

DEFAULT_TOKEN_TTL_SECONDS = 3600


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _hmac(secret: str, payload: str) -> str:
    return _b64url(hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest())


class StreamingTokenService:
    """Vystavuje streamovacie tokeny. Secret cita pri kazdom volani (rotatable)."""

    def __init__(self, ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def secret() -> str:
        return (getattr(settings, "CMEP_STREAMING_SIGNING_SECRET", "") or "").strip()

    @classmethod
    def is_configured(cls) -> bool:
        secret = cls.secret()
        return len(secret) >= 32 and "REPLACE_" not in secret

    def mint(
        self,
        *,
        user_id: UUID,
        company_id: UUID | None,
        inspection_id: UUID,
        listing_id: UUID,
        role: str,
        consent_to_record: bool = False,
        now: datetime | None = None,
    ) -> StreamingToken:
        secret = self.secret()
        if not self.is_configured():
            raise ValidationDomainError(
                "Live inspection is not configured: set CMEP_STREAMING_SIGNING_SECRET "
                "(min 32 chars) on the platform."
            )
        if role not in ("publisher", "viewer"):
            raise ValidationDomainError("Invalid inspection role")
        current = now or datetime.now()
        iat = int(current.timestamp())
        claims = {
            "sub": str(user_id),
            "companyId": str(company_id) if company_id else "",
            "insp": str(inspection_id),
            # V http mode je "offerId" totozné s ID obhliadky (rovnaké ako room.offerId
            # a ako parameter offer= v publishUrl). Streaming používa event.offerId
            # ako inspectionId pri ingeste eventov a viaže room na claims.insp.
            "offerId": str(inspection_id),
            "listingId": str(listing_id),
            "role": role,
            "rec": 1 if consent_to_record else 0,
            "iat": iat,
            "exp": iat + self.ttl_seconds,
        }
        payload = _b64url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
        token = f"{payload}.{_hmac(secret, payload)}"
        return StreamingToken(
            token=token,
            expires_in=self.ttl_seconds,
            inspection_id=inspection_id,
            role=role,
            company_id=company_id,
        )


def verify_streaming_token_self(token: str) -> dict | None:
    """Self-check overenia (pouziva sa v testoch) — rovnaka matematika ako auth.js."""
    secret = StreamingTokenService.secret()
    try:
        payload, signature = token.split(".")
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(_hmac(secret, payload), signature):
        return None
    try:
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, TypeError):
        return None
    if not claims.get("sub") or claims.get("exp", 0) * 1000 <= time.time() * 1000:
        return None
    return claims
