"""Shared helpers for AI provider gateways.

Two concerns kept out of every gateway implementation:

* ``resolve_url`` — a URL must never contain whitespace. Misconfigured env
  values often append junk after a space (e.g.
  ``https://api.mistral.ai/v1/chat/completions Default``); a URL can never
  legitimately contain a space, so we keep the first whitespace-delimited token
  and validate it is a real http(s) URL.

* ``log_http_error`` — log the provider, the HTTP status and a safe error code
  extracted from the JSON body. Headers (Authorization) and the raw body are
  NEVER logged, and the API key can never leak into logs this way.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit

_logger = logging.getLogger(__name__)


def resolve_url(raw: str | None, default: str, env_name: str) -> str:
    """Return a validated, whitespace-free http(s) URL.

    Falls back to ``default`` when ``raw`` is empty. Raises ``RuntimeError`` when
    the resolved value is not a valid http(s) URL.
    """
    value = (raw or "").strip()
    if not value:
        return default
    if any(ch.isspace() for ch in value):
        # A URL never contains whitespace; keep the first token (the URL itself).
        value = value.split()[0]
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise RuntimeError(f"{env_name} is not a valid http(s) URL")
    return value


def log_http_error(logger: logging.Logger, provider: str, error: object) -> None:
    """Log provider + HTTP status + safe error code; never headers/body/key."""
    status = getattr(error, "code", None)
    code: str | None = None
    try:
        raw = error.read()  # type: ignore[attr-defined]
        if raw:
            data = json.loads(raw.decode("utf-8", "replace"))
            if isinstance(data, dict):
                err = data.get("error")
                if isinstance(err, dict):
                    code = err.get("code") or err.get("type")
                elif isinstance(err, str):
                    code = err
    except Exception:
        code = None
    logger.warning(
        "provider=%s http_status=%s error_code=%s",
        provider,
        status,
        code if code else "unknown",
    )
