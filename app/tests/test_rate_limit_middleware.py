"""Unit testy pre rate-limit middleware a memory limiter (hermeticke)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.shared.infrastructure import rate_limit as rate_limit_mod
from app.shared.presentation.rate_limit_middleware import _match_rules


def _names(method: str, path: str) -> list[str]:
    return [name for _, _, name in _match_rules(method, path)]


def test_chat_post_matches_burst_and_hourly():
    rules = _match_rules("POST", "/api/v1/agent-platform/chat")
    by_name = {name: (limit, period) for limit, period, name in rules}
    assert set(by_name) == {"agent-chat-ip", "agent-chat-hourly"}
    assert by_name["agent-chat-ip"] == (20, 60)
    assert by_name["agent-chat-hourly"] == (120, 3600)


def test_chat_matches_pretty_path_without_api_prefix():
    # Path bez /api prefixu prejde normalizaciou tak isto.
    assert set(_names("POST", "/agent-platform/chat")) == {"agent-chat-ip", "agent-chat-hourly"}


def test_chat_subpath_is_covered():
    # Buduci stream endpoint /agent-platform/chat/xxx tiez patri pod chat limity.
    assert set(_names("POST", "/agent-platform/chat/stream")) == {
        "agent-chat-ip",
        "agent-chat-hourly",
    }


def test_voice_transcribe_matches_voice_rules():
    by_name = {
        name: (limit, period)
        for limit, period, name in _match_rules("POST", "/agent-platform/voice/transcribe")
    }
    assert by_name == {"agent-voice-ip": (10, 60), "agent-voice-hourly": (60, 3600)}


def test_voice_live_token_matches_voice_rules():
    assert set(_names("POST", "/api/v1/agent-platform/voice/token")) == {
        "agent-voice-ip",
        "agent-voice-hourly",
    }


def test_get_chat_is_not_limited():
    assert _names("GET", "/agent-platform/chat") == []


def test_unlisted_path_has_no_rules():
    assert _names("POST", "/agent-platform/unlisted") == []


def test_legacy_single_rule_still_matches():
    rules = _match_rules("POST", "/api/v1/auth/2fa/login")
    assert [(lim, per, n) for lim, per, n in rules] == [(10, 60, "2fa-login-ip")]


def test_trailing_slash_prefix_rule_matches_subpaths():
    # /chat/threads/123 sedi na chat-message (prefix /chat/threads/)
    # AJ na chat-create (podstrom pravidla /chat/threads) — obe limity platia.
    assert set(_names("POST", "/api/v1/chat/threads/123")) == {"chat-message", "chat-create"}


async def test_check_rate_limit_memory_raises_429(monkeypatch):
    # Vynutime memory backend (ziadny realny redis) — hermeticke.
    async def _none():
        return None

    monkeypatch.setattr(rate_limit_mod, "_client", _none)
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    key = "test-burst:203.0.113.7"
    rate_limit_mod._mem.clear()
    try:
        await rate_limit_mod.check_rate_limit(key, limit=2, period=60)
        await rate_limit_mod.check_rate_limit(key, limit=2, period=60)
        with pytest.raises(HTTPException) as excinfo:
            await rate_limit_mod.check_rate_limit(key, limit=2, period=60)
        assert excinfo.value.status_code == 429
    finally:
        rate_limit_mod._mem.clear()


async def test_check_rate_limit_disabled_never_raises(monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", False)
    # 100 hitov nad limit, ale disabled → ziadna vynimka.
    for _ in range(5):
        await rate_limit_mod.check_rate_limit("test-disabled:203.0.113.8", limit=1, period=60)
