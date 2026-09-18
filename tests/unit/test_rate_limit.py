"""Unit tests for the request rate limiter and client-IP resolution.

``check_rate_limit`` has two backends: Redis when reachable, otherwise an
in-process dictionary. Tests must never write to a real Redis instance, so
``_client`` is always patched for the behavioural tests.
"""

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.shared.infrastructure import rate_limit


def _request(headers=None, client=("9.9.9.9", 1234)):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": raw,
            "client": client,
        }
    )


class _FakeRedis:
    """Minimal stand-in whose pipeline reports a fixed hit count."""

    def __init__(self, count):
        self._count = count

    def pipeline(self):
        return self

    def zremrangebyscore(self, *args, **kwargs):
        return self

    def zadd(self, *args, **kwargs):
        return self

    def zcard(self, *args, **kwargs):
        return self

    def expire(self, *args, **kwargs):
        return self

    def execute(self):
        # Mirrors the (zremrangebyscore, zadd, zcard, expire) result order.
        return [0, 1, self._count, True]


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", True)
    return settings.rate_limit


@pytest.fixture
def disabled(monkeypatch):
    monkeypatch.setattr(settings.rate_limit, "enabled", False)
    return settings.rate_limit


@pytest.fixture
def mem_backend(monkeypatch):
    """Force the in-process fallback and isolate its storage."""
    monkeypatch.setattr(rate_limit, "_client", lambda: None)
    rate_limit._mem.clear()
    yield rate_limit._mem
    rate_limit._mem.clear()


@pytest.fixture
def redis_backend(monkeypatch):
    def _install(count):
        monkeypatch.setattr(rate_limit, "_client", lambda: _FakeRedis(count))

    return _install


# --------------------------------------------------------------------------
# disabled / no-op behaviour
# --------------------------------------------------------------------------


def test_disabled_limiter_never_raises(disabled, mem_backend):
    for _ in range(50):
        rate_limit.check_rate_limit("k", limit=1, period=60)


def test_disabled_limiter_does_not_touch_redis(disabled, monkeypatch):
    def _explode():
        raise AssertionError("redis must not be consulted when disabled")

    monkeypatch.setattr(rate_limit, "_client", _explode)

    rate_limit.check_rate_limit("k", limit=1, period=60)


# --------------------------------------------------------------------------
# in-process fallback
# --------------------------------------------------------------------------


def test_allows_requests_up_to_limit(enabled, mem_backend):
    for _ in range(3):
        rate_limit.check_rate_limit("k", limit=3, period=60)


def test_blocks_request_over_limit(enabled, mem_backend):
    for _ in range(2):
        rate_limit.check_rate_limit("k", limit=2, period=60)

    with pytest.raises(HTTPException) as exc:
        rate_limit.check_rate_limit("k", limit=2, period=60)

    assert exc.value.status_code == 429
    assert exc.value.detail


def test_keys_have_independent_budgets(enabled, mem_backend):
    rate_limit.check_rate_limit("a", limit=1, period=60)

    # A different key must not inherit 'a' history.
    rate_limit.check_rate_limit("b", limit=1, period=60)


def test_history_outside_window_is_pruned(enabled, mem_backend):
    # period=0 means every previously recorded hit is already stale.
    for _ in range(5):
        rate_limit.check_rate_limit("k", limit=1, period=0)


def test_explicit_limit_overrides_settings(enabled, mem_backend):
    # settings.requests defaults well above 1, so a 2nd call must be blocked.
    rate_limit.check_rate_limit("k", limit=1, period=60)

    with pytest.raises(HTTPException):
        rate_limit.check_rate_limit("k", limit=1, period=60)


def test_default_limit_is_clamped_to_twenty(enabled, mem_backend):
    """limit=None falls back to max(5, min(requests, 20)) -> 20 by default."""
    for _ in range(20):
        rate_limit.check_rate_limit("k", period=60)

    with pytest.raises(HTTPException):
        rate_limit.check_rate_limit("k", period=60)


# --------------------------------------------------------------------------
# redis backend
# --------------------------------------------------------------------------


def test_redis_backend_allows_under_limit(enabled, redis_backend):
    redis_backend(1)

    rate_limit.check_rate_limit("k", limit=5, period=60)


def test_redis_backend_blocks_over_limit(enabled, redis_backend):
    redis_backend(99)

    with pytest.raises(HTTPException) as exc:
        rate_limit.check_rate_limit("k", limit=5, period=60)

    assert exc.value.status_code == 429


def test_redis_backend_boundary_is_inclusive(enabled, redis_backend):
    """Exactly ``limit`` hits is still permitted."""
    redis_backend(5)

    rate_limit.check_rate_limit("k", limit=5, period=60)


# --------------------------------------------------------------------------
# _client
# --------------------------------------------------------------------------


def test_real_client_is_optional():
    """Redis is optional: an unreachable server must degrade to None."""
    client = rate_limit._client()

    assert client is None or hasattr(client, "ping")


# --------------------------------------------------------------------------
# client_ip
# --------------------------------------------------------------------------


def test_client_ip_prefers_forwarded_header():
    request = _request({"X-Forwarded-For": "203.0.113.5, 10.0.0.1"})

    assert rate_limit.client_ip(request) == "203.0.113.5"


def test_client_ip_falls_back_to_socket_address():
    assert rate_limit.client_ip(_request()) == "9.9.9.9"


def test_client_ip_handles_missing_client():
    assert rate_limit.client_ip(_request(client=None)) == "unknown"


def test_client_ip_handles_blank_host():
    assert rate_limit.client_ip(_request(client=("", 0))) == "unknown"


def test_client_ip_ignores_whitespace_in_header():
    request = _request({"X-Forwarded-For": "  198.51.100.7  , 10.0.0.1"})

    assert rate_limit.client_ip(request) == "198.51.100.7"
