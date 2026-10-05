"""HMAC-SHA256 signing for temporary upload URLs.

Provides short-lived signed URLs so GET /uploads/{file_id} can be
protected without breaking <img src> in the frontend. UUIDs leak
through referrer headers, server logs, and chat screenshots, so the
raw file_id is not treated as a secret.

Design:
- Token = base64url(HMAC-SHA256(secret, file_id + ":" + expires_at))
- expires_at = unix timestamp (seconds)
- Default TTL: 5 minutes
- Constant-time comparison via hmac.compare_digest
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

DEFAULT_TTL_SECONDS = 300
MAX_TTL_SECONDS = 3600


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _compute_signature(secret: str, file_id: str, expires_at: int) -> str:
    payload = f"{file_id}:{expires_at}".encode()
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _b64url_encode(digest)


def sign_file_url(file_id: str, secret: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict:
    """Return a signed URL fragment for a file_id.

    Returns:
        {
          "file_id": str,
          "expires_at": int,
          "signature": str,
          "url_path": "/uploads/<id>?expires=<ts>&sig=<sig>",
        }
    """
    if not file_id or not secret:
        raise ValueError("file_id and secret are required")

    if ttl_seconds < 1:
        ttl_seconds = DEFAULT_TTL_SECONDS

    if ttl_seconds > MAX_TTL_SECONDS:
        ttl_seconds = MAX_TTL_SECONDS

    expires_at = int(time.time()) + ttl_seconds
    signature = _compute_signature(secret, file_id, expires_at)

    return {
        "file_id": file_id,
        "expires_at": expires_at,
        "signature": signature,
        "url_path": f"/uploads/{file_id}?expires={expires_at}&sig={signature}",
    }


def verify_file_url(
    file_id: str,
    secret: str,
    expires_at: int,
    signature: str,
) -> tuple[bool, str]:
    """Verify a signed upload URL.

    Returns:
        (True, "ok") on success
        (False, reason) on failure

    Reasons: "missing", "expired", "mismatch", "invalid"
    """
    if not file_id or not secret or not signature:
        return False, "missing"

    try:
        expires_at_int = int(expires_at)
    except (TypeError, ValueError):
        return False, "invalid"

    if expires_at_int < int(time.time()):
        return False, "expired"

    expected = _compute_signature(secret, file_id, expires_at_int)

    if not hmac.compare_digest(expected, signature):
        return False, "mismatch"

    return True, "ok"


__all__ = [
    "DEFAULT_TTL_SECONDS",
    "MAX_TTL_SECONDS",
    "sign_file_url",
    "verify_file_url",
]
