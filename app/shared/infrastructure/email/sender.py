"""Best-effort SMTP sender. Without credentials logs and returns False."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, body: str) -> bool:
    host = getattr(settings, "SMTP_HOST", "")
    port = int(getattr(settings, "SMTP_PORT", 587))
    user = getattr(settings, "SMTP_USERNAME", "")
    password = getattr(settings, "SMTP_PASSWORD", "")
    from_address = getattr(settings, "EMAIL_FROM", "") or user
    use_tls = bool(getattr(settings, "SMTP_USE_TLS", True))

    if not host or not user or not password:
        logger.warning(
            "EMAIL not configured – message to %s not sent. subject=%s",
            to,
            subject,
        )
        # Bezpecnost: telo spravy obsahuje password-reset token. Nikdy ho
        # nelogujeme mimo development prostredia.
        if settings.is_development:
            logger.info("EMAIL_DEV_BODY to=%s\n%s", to, body)
        else:
            logger.info("EMAIL body suppressed in non-development environment (to=%s)", to)
        return False

    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        logger.exception("send_email failed: %s", exc)
        return False
