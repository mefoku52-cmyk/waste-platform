"""Transactional email sender.

Transactional = user-triggered email (inquiry, verification, password reset).
NIE cold outreach. Preto NEPOUZIVA lead_outreach daily limit.

Priorita:
1. Resend (ak RESEND_API_KEY je nastaveny)
2. SMTP (ak SMTP_HOST/USER/PASSWORD su nastavene)
3. Ziadny - vrati False, ale NIKDY nezlyha (best-effort).
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.shared.infrastructure.email.sender import send_email as send_via_smtp

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


async def send_transactional_email(
    *,
    to: str,
    subject: str,
    body: str,
    reply_to: str | None = None,
) -> bool:
    """Posle jeden transakcny email. Best-effort, nikdy nezlyha.

    Vrati True ak bol email odoslany (cez Resend alebo SMTP),
    False ak nic nebolo nakonfigurovane alebo vsetko zlyhalo.
    """
    api_key = (settings.RESEND_API_KEY or "").strip()
    from_email = (settings.RESEND_FROM_EMAIL or "").strip()

    if api_key and from_email:
        try:
            return await _send_via_resend(
                api_key=api_key,
                from_email=from_email,
                to=to,
                subject=subject,
                body=body,
                reply_to=reply_to,
            )
        except Exception:
            logger.exception("transactional resend failed, trying SMTP fallback")

    try:
        return send_via_smtp(to=to, subject=subject, body=body)
    except Exception:
        logger.exception("transactional smtp failed")
        return False


async def _send_via_resend(
    *,
    api_key: str,
    from_email: str,
    to: str,
    subject: str,
    body: str,
    reply_to: str | None,
) -> bool:
    from_name = (getattr(settings, "RESEND_FROM_NAME", "") or "CMEP").strip()
    from_header = f"{from_name} <{from_email}>" if from_name else from_email

    payload: dict[str, object] = {
        "from": from_header,
        "to": [to],
        "subject": subject,
        "text": body,
    }
    effective_reply_to = reply_to or (getattr(settings, "RESEND_REPLY_TO", "") or "").strip()
    if effective_reply_to:
        payload["reply_to"] = effective_reply_to

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(RESEND_URL, json=payload, headers=headers)

    if resp.status_code >= 400:
        short = ""
        try:
            data = resp.json()
            short = str(data.get("message") or data.get("error") or "")[:200]
        except Exception:
            short = resp.text[:200]
        logger.warning("transactional resend error %s: %s", resp.status_code, short)
        return False

    return True
