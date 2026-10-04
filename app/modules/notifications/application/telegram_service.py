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

from app.core.config import settings
from app.modules.notifications.infrastructure.telegram_client import (
    TelegramClient,
)

logger = logging.getLogger(__name__)


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

        client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        return await client.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CHAT_ID,
            text=text,
        )

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


__all__ = ["TelegramService"]
