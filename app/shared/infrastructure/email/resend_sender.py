"""Resend email sender with daily rate limit.

Legal B2B outreach. Never bulk. Never auto-loop.
Each send is one call, one audit record.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


@dataclass(frozen=True, slots=True)
class SendResult:
    ok: bool
    message: str
    remaining_today: int | None = None


async def count_sent_today(session: AsyncSession) -> int:
    """Count lead_outreach.send events in the last 24h window (UTC day).

    Cita z activity_events.event_type (stlpec je event_type, NIE action —
    action je stlpec v admin_audit_entries a v activity_events neexistuje).
    """
    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        r = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM activity_events
                WHERE event_type = 'lead_outreach.send'
                  AND created_at >= :start
                """
            ),
            {"start": start_of_day.replace(tzinfo=None)},
        )
        return int(r.scalar() or 0)
    except Exception:
        logger.exception("count_sent_today failed")
        return 0


async def send_via_resend(
    *,
    session: AsyncSession,
    to: str,
    subject: str,
    body: str,
) -> SendResult:
    """Send one email via Resend, respecting daily limit and enabled flag.

    Returns SendResult. Never raises. Never logs the body.
    """
    if not settings.LEAD_OUTREACH_ENABLED:
        return SendResult(
            ok=False, message="Lead outreach je vypnuty (LEAD_OUTREACH_ENABLED=false)."
        )

    api_key = (settings.RESEND_API_KEY or "").strip()
    from_email = (settings.RESEND_FROM_EMAIL or "").strip()
    if not api_key or not from_email:
        return SendResult(
            ok=False, message="Resend nie je nakonfigurovany (chýba API kľúč alebo odosielateľ)."
        )

    limit = max(1, int(settings.LEAD_OUTREACH_DAILY_LIMIT or 30))
    sent_today = await count_sent_today(session)
    if sent_today >= limit:
        return SendResult(
            ok=False,
            message=f"Denný limit dosiahnutý ({sent_today}/{limit}). Skús zajtra.",
            remaining_today=0,
        )

    # Resend odmieta prázdne telo (422 Missing html or text). Over to pred requestom.
    if not body or not body.strip():
        return SendResult(
            ok=False,
            message="Email nemá telo (draft_body je prázdny). Vygeneruj draft alebo vyplň text.",
        )

    from_header = f"{settings.RESEND_FROM_NAME} <{from_email}>"

    reply_to = (getattr(settings, "RESEND_REPLY_TO", "") or "").strip()

    payload: dict[str, object] = {
        "from": from_header,
        "to": [to],
        "subject": subject,
        "text": body,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(RESEND_URL, json=payload, headers=headers)
    except Exception as exc:
        logger.exception("resend request failed")
        return SendResult(ok=False, message=f"Resend request zlyhal: {type(exc).__name__}")

    if resp.status_code >= 400:
        # Bezpecnost: neposielame telo chyby spat pouzivatelovi v plnom zneni.
        short = ""
        try:
            data = resp.json()
            short = str(data.get("message") or data.get("error") or "")[:200]
        except Exception:
            short = resp.text[:200]
        logger.warning("resend error %s: %s", resp.status_code, short)
        return SendResult(ok=False, message=f"Resend odmietol ({resp.status_code}).")

    remaining = limit - sent_today - 1
    return SendResult(ok=True, message="Email odoslaný.", remaining_today=max(0, remaining))
