"""Unit tests for the Resend daily-limit counter (BUG-02/A).

Bug A: count_sent_today counted `activity_events.action`, a column that does
not exist (the column is `event_type`). The SQL error was swallowed by the
except clause, so count_sent_today always returned 0 and the daily limit was
never enforced.

These tests pin:
* the query reads activity_events.event_type (not action),
* the limit blocks a send once the day's quota is reached,
* the limit allows a send while under the quota,
* the counter degrades to 0 (never raises) on a backend error.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.shared.infrastructure.email import resend_sender
from app.shared.infrastructure.email.resend_sender import (
    count_sent_today,
    send_via_resend,
)


class _ScalarSession:
    """Minimal fake AsyncSession that records executed SQL and returns a scalar."""

    def __init__(self, value):
        self._value = value
        self.calls: list[tuple[str, dict | None]] = []

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        result = MagicMock()
        result.scalar.return_value = self._value
        return result


class _BoomSession:
    async def execute(self, statement, params=None):
        raise RuntimeError('relation "activity_events" does not exist')


def _async_count(value):
    async def _inner(session):
        return value

    return _inner


class _Resp:
    status_code = 200

    def json(self):
        return {"id": "abc"}


class _OkClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        return _Resp()


@pytest.fixture
def resend_ready(monkeypatch):
    """Enable Resend with deterministic settings for limit tests."""
    monkeypatch.setattr(settings, "LEAD_OUTREACH_ENABLED", True)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "test-key")
    monkeypatch.setattr(settings, "RESEND_FROM_EMAIL", "noreply@cmep.dev")
    monkeypatch.setattr(settings, "RESEND_FROM_NAME", "CMEP")
    return settings


# --------------------------------------------------------------------------
# count_sent_today — column name
# --------------------------------------------------------------------------


async def test_count_sent_today_uses_event_type():
    session = _ScalarSession(3)

    result = await count_sent_today(session)

    assert result == 3
    sql = session.calls[0][0]
    assert "event_type" in sql
    assert "event_type = 'lead_outreach.send'" in sql
    # The buggy column must be gone.
    assert "action" not in sql


async def test_count_sent_today_passes_start_bound():
    session = _ScalarSession(0)

    await count_sent_today(session)

    _, params = session.calls[0]
    assert params is not None and "start" in params


async def test_count_sent_today_returns_zero_on_backend_error():
    # Never raises: a broken counter must not break sending.
    assert await count_sent_today(_BoomSession()) == 0


# --------------------------------------------------------------------------
# send_via_resend — daily limit enforcement
# --------------------------------------------------------------------------


async def test_daily_limit_blocks_over_limit(resend_ready, monkeypatch):
    monkeypatch.setattr(settings, "LEAD_OUTREACH_DAILY_LIMIT", 2)
    monkeypatch.setattr(resend_sender, "count_sent_today", _async_count(2))

    with patch.object(resend_sender.httpx, "AsyncClient") as mock_client:
        result = await send_via_resend(session=None, to="x@y.sk", subject="Hi", body="Body")

    assert result.ok is False
    assert result.remaining_today == 0
    assert "limit" in result.message.lower()
    # No HTTP call may happen once the limit is hit.
    mock_client.assert_not_called()


async def test_daily_limit_allows_under_limit(resend_ready, monkeypatch):
    monkeypatch.setattr(settings, "LEAD_OUTREACH_DAILY_LIMIT", 5)
    monkeypatch.setattr(resend_sender, "count_sent_today", _async_count(1))

    with patch.object(resend_sender.httpx, "AsyncClient", _OkClient):
        result = await send_via_resend(session=None, to="x@y.sk", subject="Hi", body="Body")

    assert result.ok is True
    # limit - sent_today - 1 = 5 - 1 - 1
    assert result.remaining_today == 3


async def test_send_does_not_count_when_disabled(resend_ready, monkeypatch):
    monkeypatch.setattr(settings, "LEAD_OUTREACH_ENABLED", False)
    monkeypatch.setattr(resend_sender, "count_sent_today", _async_count(0))

    with patch.object(resend_sender.httpx, "AsyncClient") as mock_client:
        result = await send_via_resend(session=None, to="x@y.sk", subject="Hi", body="Body")

    assert result.ok is False
    mock_client.assert_not_called()
