"""Async HTTP client pre Telegram Bot API.

Ziadne exceptiony von — pri chybe sa loguje WARNING a vrati False/None.
Notifikacie nesmu nikdy zhodit hlavny request.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"
_TIMEOUT = 10.0


def _mask_url(url: str) -> str:
    """Skry token v URL pre logy. Vzdy vracia bezpecny tvar."""
    if "/bot" in url:
        # telegram API: /bot<TOKEN>/method
        parts = url.split("/bot", 1)
        if len(parts) == 2:
            return (
                f"{parts[0]}/bot[REDACTED]/{parts[1].split('/', 1)[-1] if '/' in parts[1] else ''}"
            )
    return "[REDACTED_URL]"


class TelegramClient:
    """Tenky wrapper nad Telegram Bot API."""

    def __init__(self, bot_token: str) -> None:
        self._token = (bot_token or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self._token)

    def _url(self, method: str) -> str:
        return f"{_API_BASE}/bot{self._token}/{method}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
    ) -> bool:
        """Posli spravu. Vrat True ak Telegram odpovedal ok=true."""
        if not self._token or not chat_id or not text:
            return False

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    self._url("sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": text[:4096],
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True,
                    },
                )
        except Exception as exc:
            logger.warning("Telegram send_message failed: %s", _mask_url(str(exc)))
            return False

        if resp.status_code != 200:
            logger.warning(
                "Telegram send_message HTTP %s: %s",
                resp.status_code,
                resp.text[:200],
            )
            return False

        try:
            payload = resp.json()
        except Exception:
            logger.warning("Telegram send_message: invalid JSON")
            return False

        return bool(payload.get("ok"))

    async def get_me(self) -> dict | None:
        """Vrat info o botovi alebo None."""
        if not self._token:
            return None

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(self._url("getMe"))
        except Exception as exc:
            logger.warning("Telegram get_me failed: %s", _mask_url(str(exc)))
            return None

        if resp.status_code != 200:
            logger.warning("Telegram get_me HTTP %s", resp.status_code)
            return None

        try:
            payload = resp.json()
        except Exception:
            return None

        if not payload.get("ok"):
            return None

        return payload.get("result")


__all__ = ["TelegramClient"]
