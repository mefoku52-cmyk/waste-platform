"""Turnstile verifier — disabled path, guard clauses and HTTP verify path.

Ziadne realne Cloudflare volanie: httpx.AsyncClient je vzdy nahradeny fake
triedou (rovnaky vzor ako FakeResponse v test_website_contact_crawler.py).
"""

import asyncio

import httpx
import pytest

from app.core.config import settings
from app.shared.infrastructure import turnstile


class FakeResponse:
    """Minimalna nahrada httpx.Response pre mockovane volania."""

    def __init__(self, status_code: int = 200, payload=None, json_error=None) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


def _fake_client(response: FakeResponse | None = None, error: Exception | None = None):
    """Postav fake httpx.AsyncClient; vrat ho spolu so zoznamom requestov."""
    calls: list[dict] = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self.init_kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, data=None, **kwargs):
            calls.append({"url": url, "data": data, "init": self.init_kwargs})
            if error is not None:
                raise error
            return response

    return FakeAsyncClient, calls


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Kazde realne HTTP volanie musi zlyhat - testy nesmu siet."""

    def _fail(*args, **kwargs):
        raise AssertionError(f"real HTTP request attempted: {args} {kwargs}")

    monkeypatch.setattr(httpx, "AsyncClient", _fail)


@pytest.fixture
def turnstile_enabled(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "TURNSTILE_SECRET_KEY", "fake-secret", raising=False)
    return settings


# --- Vypnuty Turnstile --------------------------------------------------


def test_turnstile_disabled_returns_true(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", False, raising=False)
    result = asyncio.run(turnstile.verify_turnstile(None))
    assert result is True


def test_turnstile_disabled_ignores_token(monkeypatch):
    monkeypatch.setattr(settings, "TURNSTILE_ENABLED", False, raising=False)
    result = asyncio.run(turnstile.verify_turnstile("garbage-token"))
    assert result is True


# --- Guard clauses (bez HTTP) -------------------------------------------


def test_turnstile_enabled_missing_token_returns_false(turnstile_enabled):
    result = asyncio.run(turnstile.verify_turnstile(None))
    assert result is False


def test_turnstile_enabled_empty_token_returns_false(turnstile_enabled):
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


# --- HTTP verifikacna cesta ---------------------------------------------


def test_verify_success_returns_true(turnstile_enabled, monkeypatch):
    client, calls = _fake_client(FakeResponse(payload={"success": True}))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("good-token")) is True

    assert len(calls) == 1
    assert calls[0]["url"] == turnstile.TURNSTILE_VERIFY_URL
    assert calls[0]["data"] == {"secret": "fake-secret", "response": "good-token"}
    assert calls[0]["init"]["timeout"] == 5.0


def test_verify_valid_json_success_false_returns_false(turnstile_enabled, monkeypatch):
    response = FakeResponse(payload={"success": False, "error-codes": ["invalid-input-response"]})
    client, calls = _fake_client(response)
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("bad-token")) is False
    assert len(calls) == 1


def test_verify_sends_remote_ip_when_provided(turnstile_enabled, monkeypatch):
    client, calls = _fake_client(FakeResponse(payload={"success": True}))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok", "1.2.3.4")) is True
    assert calls[0]["data"]["remoteip"] == "1.2.3.4"


def test_verify_omits_remote_ip_when_not_provided(turnstile_enabled, monkeypatch):
    client, calls = _fake_client(FakeResponse(payload={"success": True}))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is True
    assert "remoteip" not in calls[0]["data"]


def test_verify_network_timeout_returns_false(turnstile_enabled, monkeypatch):
    client, _calls = _fake_client(error=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is False


def test_verify_connection_error_returns_false(turnstile_enabled, monkeypatch):
    client, _calls = _fake_client(error=httpx.ConnectError("connection refused"))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is False


def test_verify_invalid_json_returns_false(turnstile_enabled, monkeypatch):
    response = FakeResponse(json_error=ValueError("Expecting value: line 1 column 1"))
    client, _calls = _fake_client(response)
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is False


def test_verify_rate_limit_429_returns_false(turnstile_enabled, monkeypatch):
    response = FakeResponse(
        status_code=429,
        payload={"success": False, "error-codes": ["rate-limited"]},
    )
    client, _calls = _fake_client(response)
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is False


def test_verify_unexpected_payload_shape_returns_false(turnstile_enabled, monkeypatch):
    """Chybajuci 'success' kluc -> False, ziadna vynimka."""
    client, _calls = _fake_client(FakeResponse(payload={"error-codes": []}))
    monkeypatch.setattr(turnstile.httpx, "AsyncClient", client)

    assert asyncio.run(turnstile.verify_turnstile("tok")) is False
