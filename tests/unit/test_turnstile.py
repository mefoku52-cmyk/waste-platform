"""Turnstile verifier — default behavior when disabled."""

import asyncio

from app.core.config import settings
from app.shared.infrastructure import turnstile


def test_turnstile_disabled_returns_true(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", False, raising=False)
    result = asyncio.run(turnstile.verify_turnstile(None))
    assert result is True


def test_turnstile_disabled_ignores_token(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", False, raising=False)
    result = asyncio.run(turnstile.verify_turnstile("garbage-token"))
    assert result is True


def test_turnstile_enabled_missing_token_returns_false(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "fake-secret", raising=False)
    result = asyncio.run(turnstile.verify_turnstile(None))
    assert result is False


def test_turnstile_enabled_empty_token_returns_false(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "fake-secret", raising=False)
    result = asyncio.run(turnstile.verify_turnstile(""))
    assert result is False


def test_turnstile_enabled_missing_secret_returns_false(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "", raising=False)
    result = asyncio.run(turnstile.verify_turnstile("some-token"))
    assert result is False


def test_turnstile_verify_url_constant():
    assert "cloudflare.com" in turnstile.TURNSTILE_VERIFY_URL
    assert "siteverify" in turnstile.TURNSTILE_VERIFY_URL
