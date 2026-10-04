"""Admin endpoints pre Telegram diagnostiku.

Bezpecnost: NIKDY nevracia hodnotu tokenu ani cast. Len booly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.modules.notifications.application.telegram_service import (
    TelegramService,
)
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import is_platform_admin

router = APIRouter(prefix="/admin/telegram", tags=["admin-telegram"])


class TelegramTestResponse(BaseModel):
    ok: bool
    message: str


class TelegramStatusResponse(BaseModel):
    enabled: bool
    bot_configured: bool
    chat_configured: bool


def _require_admin(current_user) -> None:
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform admin access required")


@router.post("/test", response_model=TelegramTestResponse)
async def telegram_test(
    current_user=Depends(require_current_user),
) -> TelegramTestResponse:
    """Posli testovaciu spravu na admin chat. Admin only."""
    _require_admin(current_user)

    if not TelegramService.is_enabled():
        return TelegramTestResponse(
            ok=False,
            message="Telegram je vypnuty alebo chyba konfiguracia "
            "(TELEGRAM_ENABLED / BOT_TOKEN / ADMIN_CHAT_ID).",
        )

    ok = await TelegramService.notify_test()

    if ok:
        return TelegramTestResponse(ok=True, message="Test sprava odoslana.")

    return TelegramTestResponse(
        ok=False,
        message="Telegram API volanie zlyhalo — pozri server logy.",
    )


@router.get("/status", response_model=TelegramStatusResponse)
async def telegram_status(
    current_user=Depends(require_current_user),
) -> TelegramStatusResponse:
    """Vrat stav Telegram konfiguracie bez odhalenia tokenu. Admin only."""
    _require_admin(current_user)

    return TelegramStatusResponse(
        enabled=bool(settings.TELEGRAM_ENABLED),
        bot_configured=bool((settings.TELEGRAM_BOT_TOKEN or "").strip()),
        chat_configured=bool((settings.TELEGRAM_ADMIN_CHAT_ID or "").strip()),
    )
