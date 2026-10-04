"""Testy pre TelegramService — notifikacie z CMEP.

Kazdy test mockuje httpx.AsyncClient, aby nesiel realny request.
Klucove pravidlo: notifikacie NIKDY nezhodia hlavny flow.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.notifications.application.telegram_service import (
    TelegramService,
)
from app.modules.notifications.infrastructure.telegram_client import (
    TelegramClient,
)


@pytest.fixture
def fake_settings(monkeypatch):
    """Nastav fake Telegram config na settings objekte."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_ENABLED", True)
    monkeypatch.setattr(config_mod.settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(config_mod.settings, "TELEGRAM_ADMIN_CHAT_ID", "123456")
    yield config_mod.settings


def test_is_enabled_when_config_complete(fake_settings):
    """Vsetky 3 polia OK -> True."""
    assert TelegramService.is_enabled() is True


def test_is_enabled_false_when_disabled(monkeypatch):
    """TELEGRAM_ENABLED=False -> False aj s tokenom."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(config_mod.settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(config_mod.settings, "TELEGRAM_ADMIN_CHAT_ID", "123456")

    assert TelegramService.is_enabled() is False


@pytest.mark.asyncio
async def test_notify_skips_when_disabled(monkeypatch):
    """Ak disabled, notify() vrati False a NESPRAVI HTTP request."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_ENABLED", False)

    with patch(
        "app.modules.notifications.infrastructure.telegram_client.httpx.AsyncClient"
    ) as mock_client:
        result = await TelegramService.notify("hello")

    assert result is False
    mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_notify_sends_when_enabled(fake_settings):
    """Mock httpx POST -> 200 ok=true -> notify() vrati True."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"ok": True, "result": {}}

    mock_async_client = MagicMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.post = AsyncMock(return_value=fake_response)

    with patch(
        "app.modules.notifications.infrastructure.telegram_client.httpx.AsyncClient",
        return_value=mock_async_client,
    ):
        result = await TelegramService.notify("hello")

    assert result is True
    mock_async_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_client_handles_http_error(fake_settings):
    """HTTP 500 -> vrati False, NIKDY neraises."""
    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "Internal Server Error"

    mock_async_client = MagicMock()
    mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
    mock_async_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.post = AsyncMock(return_value=fake_response)

    with patch(
        "app.modules.notifications.infrastructure.telegram_client.httpx.AsyncClient",
        return_value=mock_async_client,
    ):
        client = TelegramClient("test-token")
        result = await client.send_message("123", "hello")

    assert result is False
