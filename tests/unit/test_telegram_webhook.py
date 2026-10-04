"""Testy pre Telegram webhook endpoint a rate limiting.

Bezpecnostne pravidla:
- Webhook NIKDY neprijme request bez spravneho secret tokenu
- Webhook je 503 ak secret nie je nakonfigurovany (nedovolime open)
- Rate limit zabrani notifikacnej slucke
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.notifications.application.telegram_service import (
    _RATE_LIMIT_MAX,
    _RATE_TIMESTAMPS,
    _rate_allowed,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Kazdy test zacina s prazdnym rate limit bucketom."""
    _RATE_TIMESTAMPS.clear()
    yield
    _RATE_TIMESTAMPS.clear()


# ═══════════════════════════════════════════════════════════
# WEBHOOK
# ═══════════════════════════════════════════════════════════


def test_webhook_503_when_secret_not_configured(monkeypatch):
    """Ak TELEGRAM_WEBHOOK_SECRET je prazdny, endpoint je 503."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_WEBHOOK_SECRET", "")

    resp = client.post("/api/v1/admin/telegram/webhook", json={"update_id": 1})

    assert resp.status_code == 503


def test_webhook_403_when_secret_mismatch(monkeypatch):
    """Zly secret token -> 403, sprava sa neprijme."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_WEBHOOK_SECRET", "correct-secret-1234567890")

    resp = client.post(
        "/api/v1/admin/telegram/webhook",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )

    assert resp.status_code == 403


def test_webhook_403_when_no_secret_header(monkeypatch):
    """Chybajuca hlavicka -> 403."""
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "TELEGRAM_WEBHOOK_SECRET", "correct-secret-1234567890")

    resp = client.post("/api/v1/admin/telegram/webhook", json={"update_id": 1})

    assert resp.status_code == 403


def test_webhook_200_with_correct_secret(monkeypatch):
    """Spravny secret -> 200 a ok=true."""
    from app.core import config as config_mod

    secret = "correct-secret-1234567890"
    monkeypatch.setattr(config_mod.settings, "TELEGRAM_WEBHOOK_SECRET", secret)

    resp = client.post(
        "/api/v1/admin/telegram/webhook",
        json={"update_id": 123, "message": {"text": "/start"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": secret},
    )

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


# ═══════════════════════════════════════════════════════════
# RATE LIMIT
# ═══════════════════════════════════════════════════════════


def test_rate_limit_allows_under_max():
    """Prvych _RATE_LIMIT_MAX volani prejde."""
    for _i in range(_RATE_LIMIT_MAX):
        assert _rate_allowed("chat-1") is True


def test_rate_limit_blocks_at_max():
    """Po prekroceni limitu je volanie zamietnute."""
    for _ in range(_RATE_LIMIT_MAX):
        _rate_allowed("chat-2")

    assert _rate_allowed("chat-2") is False


def test_rate_limit_isolated_per_chat():
    """Jeden chat nespotrebuje limit druhemu."""
    for _ in range(_RATE_LIMIT_MAX):
        _rate_allowed("chat-a")

    # chat-a je na limite
    assert _rate_allowed("chat-a") is False
    # chat-b je stale prazdny
    assert _rate_allowed("chat-b") is True


def test_rate_limit_window_expires(monkeypatch):
    """Po uplynuti okna sa bucket vycisti."""
    import app.modules.notifications.application.telegram_service as svc

    # Napln bucket
    for _ in range(_RATE_LIMIT_MAX):
        _rate_allowed("chat-3")
    assert _rate_allowed("chat-3") is False

    # Posun cas o hodinu + 1 sekunda
    real_time = time.monotonic()
    monkeypatch.setattr(svc.time, "monotonic", lambda: real_time + 3601.0)

    assert _rate_allowed("chat-3") is True
