"""Resend sender tests – no real HTTP calls."""

from __future__ import annotations

from app.shared.infrastructure.email import resend_sender


class _FakeSession:
    def __init__(self, count: int) -> None:
        self._count = count

    async def execute(self, *args, **kwargs):
        class _R:
            def __init__(self, v: int) -> None:
                self._v = v

            def scalar(self) -> int:
                return self._v

        return _R(self._count)


class _FakeSettings:
    def __init__(
        self,
        *,
        enabled: bool,
        api_key: str,
        from_email: str,
        limit: int,
    ) -> None:
        self.LEAD_OUTREACH_ENABLED = enabled
        self.RESEND_API_KEY = api_key
        self.RESEND_FROM_EMAIL = from_email
        self.RESEND_FROM_NAME = "CMEP"
        self.LEAD_OUTREACH_DAILY_LIMIT = limit


import pytest


@pytest.mark.asyncio
async def test_disabled_returns_false(monkeypatch) -> None:
    monkeypatch.setattr(
        resend_sender,
        "settings",
        _FakeSettings(enabled=False, api_key="re_x", from_email="a@b.sk", limit=30),
    )
    result = await resend_sender.send_via_resend(
        session=_FakeSession(0), to="x@y.sk", subject="s", body="b"
    )
    assert result.ok is False
    assert "vypnuty" in result.message.lower()


@pytest.mark.asyncio
async def test_no_api_key_returns_false(monkeypatch) -> None:
    monkeypatch.setattr(
        resend_sender,
        "settings",
        _FakeSettings(enabled=True, api_key="", from_email="a@b.sk", limit=30),
    )
    result = await resend_sender.send_via_resend(
        session=_FakeSession(0), to="x@y.sk", subject="s", body="b"
    )
    assert result.ok is False


@pytest.mark.asyncio
async def test_daily_limit_blocks(monkeypatch) -> None:
    monkeypatch.setattr(
        resend_sender,
        "settings",
        _FakeSettings(enabled=True, api_key="re_x", from_email="a@b.sk", limit=30),
    )
    result = await resend_sender.send_via_resend(
        session=_FakeSession(30), to="x@y.sk", subject="s", body="b"
    )
    assert result.ok is False
    assert "limit" in result.message.lower()
    assert result.remaining_today == 0


def test_default_send_result_dataclass() -> None:
    r = resend_sender.SendResult(ok=True, message="x", remaining_today=5)
    assert r.ok is True
    assert r.remaining_today == 5
