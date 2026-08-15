"""Best-effort SMTP sender. Without credentials logs and returns False."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, body: str) -> bool:
    host = settings.email.smtp_host
    user = settings.email.smtp_user
    password = settings.email.smtp_password
    if not user or not password:
        logger.warning("EMAIL not configured – message to %s not sent. subject=%s", to, subject)
        logger.info("EMAIL_DEV_BODY to=%s\n%s", to, body)
        return False
    msg = EmailMessage()
    msg["From"] = settings.email.from_address
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, settings.email.smtp_port, timeout=20) as smtp:
            if settings.email.use_tls:
                smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as exc:
        logger.exception("send_email failed: %s", exc)
        return False
