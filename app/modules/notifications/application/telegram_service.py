"""High-level Telegram notifikacie pre CMEP.

Pouzitie:
    from app.modules.notifications.application.telegram_service import (
        TelegramService,
    )
    await TelegramService.notify_discovery(saved=5, duplicates=1, ...)

Vsetko je fire-and-forget safe: ak Telegram nie je nakonfigurovany
alebo zlyha, vrati False a hlavny flow pokracuje.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from app.core.config import settings
from app.modules.notifications.infrastructure.telegram_client import (
    TelegramClient,
)

logger = logging.getLogger(__name__)

# Rate limit: max 20 sprav / hodinu na chat_id. Chrani admina pred
# spamom, ak by nejaky bug sposobil notifikacnu slucku.
_RATE_LIMIT_MAX = 20
_RATE_LIMIT_WINDOW = 3600.0
_RATE_TIMESTAMPS: dict[str, deque[float]] = defaultdict(deque)


def _rate_allowed(chat_id: str) -> bool:
    """True ak chat_id este nespotreboval limit v okne."""
    now = time.monotonic()
    bucket = _RATE_TIMESTAMPS[chat_id]

    while bucket and (now - bucket[0]) > _RATE_LIMIT_WINDOW:
        bucket.popleft()

    if len(bucket) >= _RATE_LIMIT_MAX:
        return False

    bucket.append(now)
    return True


class TelegramService:
    """Staticka fasada nad TelegramClient."""

    @staticmethod
    def is_enabled() -> bool:
        """True len ak su vsetky 3 podmienky splnene."""
        return bool(
            settings.TELEGRAM_ENABLED
            and (settings.TELEGRAM_BOT_TOKEN or "").strip()
            and (settings.TELEGRAM_ADMIN_CHAT_ID or "").strip()
        )

    @staticmethod
    async def notify(text: str) -> bool:
        """Posli lubovolny text na admin chat. Vrat True ak ok."""
        if not TelegramService.is_enabled():
            return False

        chat_id = settings.TELEGRAM_ADMIN_CHAT_ID

        if not _rate_allowed(chat_id):
            logger.warning(
                "Telegram rate limit (%s msgs/h) — sprava zahodena",
                _RATE_LIMIT_MAX,
            )
            return False

        client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        return await client.send_message(chat_id=chat_id, text=text)

    @staticmethod
    async def notify_discovery(
        saved: int,
        duplicates: int,
        per_category: dict[str, int] | None = None,
    ) -> bool:
        """Notifikacia po ZS category discovery."""
        parts = [
            "📊 <b>ZS discovery</b>",
            f"Noví: <b>{saved}</b>",
            f"Duplikáty: {duplicates}",
        ]
        if per_category:
            cat_lines = "\n".join(f"  • {slug}: {count}" for slug, count in per_category.items())
            parts.append(f"<pre>{cat_lines}</pre>")
        return await TelegramService.notify("\n".join(parts))

    @staticmethod
    async def notify_drafts(drafted: int, failed: int, skipped: int) -> bool:
        """Notifikacia po batch draft."""
        return await TelegramService.notify(
            f"✍️ <b>Drafty pripravené</b>\n"
            f"Hotové: <b>{drafted}</b>\n"
            f"Zlyhalo: {failed}\n"
            f"Preskočené: {skipped}"
        )

    @staticmethod
    async def notify_sent(to_email: str, ok: bool) -> bool:
        """Notifikacia po odoslani emailu."""
        icon = "✅" if ok else "❌"
        status = "odoslaný" if ok else "zlyhal"
        return await TelegramService.notify(f"{icon} Email {status}: {to_email}")

    @staticmethod
    async def notify_test() -> bool:
        """Testovacia sprava pre UI tlacidlo."""
        return await TelegramService.notify("🔔 <b>CMEP test</b>\nTelegram bot funguje správne.")

    @staticmethod
    async def notify_alert(
        *,
        title: str,
        message: str,
        level: str = "warning",
    ) -> bool:
        """Generic alert with severity icon. Levels: info, warning, error."""
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}
        icon = icons.get(level, "⚠️")
        return await TelegramService.notify(f"{icon} <b>{title}</b>\n\n{message}")

    @staticmethod
    async def notify_pipeline_failure(*, job_name: str, error: str) -> bool:
        """Scheduled job failure alert. Error is truncated to 500 chars."""
        return await TelegramService.notify_alert(
            title=f"Pipeline zlyhal: {job_name}",
            message=f"<code>{(error or 'unknown')[:500]}</code>",
            level="error",
        )


__all__ = ["TelegramService"]
