"""Cloudflare Turnstile verifier.

Turnstile je captcha, ktoru Cloudflare poskytuje zdarma.
Backend dostane token z frontendu a overi ho u Cloudflare.

Zapnutie:
  1. Cloudflare dashboard -> Turnstile -> Add site -> ziskas
     Site Key (verejny, pre frontend) a Secret Key (sukromny, pre backend).
  2. Render env: TURNSTILE_ENABLED=true, TURNSTILE_SECRET_KEY=<secret>
  3. Frontend: pouzi Site Key v <Turnstile> widget-e na /register

Ak TURNSTILE_ENABLED=false (default), verifikacia sa preskoci a vsetko
funguje ako predtym. Zapnutie je jednosmerne cez env, nie cez kod.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> bool:
    """Vráti True ak je token platny alebo ak je Turnstile vypnuty.

    Ak je Turnstile zapnuty a token chyba/je neplatny -> False.
    """
    if not getattr(settings, "TURNSTILE_ENABLED", False):
        return True

    if not token:
        logger.warning("Turnstile enabled but no token provided")
        return False

    secret = getattr(settings, "TURNSTILE_SECRET_KEY", "")
    if not secret:
        logger.error("Turnstile enabled but TURNSTILE_SECRET_KEY missing")
        return False

    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(TURNSTILE_VERIFY_URL, data=data)
            payload = resp.json()
    except Exception:
        logger.exception("Turnstile verification request failed")
        return False

    ok = bool(payload.get("success"))
    if not ok:
        logger.warning("Turnstile rejected: %s", payload.get("error-codes"))
    return ok
