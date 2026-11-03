"""HMAC-SHA256 signing for webhook payloads with replay protection."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import orjson


def sign_payload(secret: str, payload: dict[str, Any], timestamp: int | None = None) -> tuple[str, int]:
    """Return (signature, timestamp)."""
    ts = timestamp or int(time.time())
    body = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    message = f"{ts}.".encode() + body
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return signature, ts


def verify_signature(secret: str, payload: dict[str, Any], signature: str, timestamp: int, tolerance: int = 300) -> bool:
    """Verify signature and reject old timestamps (replay protection)."""
    now = int(time.time())
    if abs(now - timestamp) > tolerance:
        return False
    expected, _ = sign_payload(secret, payload, timestamp)
    return hmac.compare_digest(expected, signature)