"""TwoFactorService unit tests — pure logic with fake session."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.auth.application.two_factor import (
    BACKUP_CODE_COUNT,
    TwoFactorService,
)


class _FakeRow:
    def __init__(self):
        self.user_id = "user-1"
        self.secret = ""
        self.enabled = False
        self.backup_codes = None
        self.verified_at = None
        self.created_at = datetime.now(UTC).replace(tzinfo=None)
        self.updated_at = datetime.now(UTC).replace(tzinfo=None)


class _FakeSession:
    def __init__(self):
        self._row: _FakeRow | None = None
        self.commits = 0

    async def get(self, model, key):
        if self._row and self._row.user_id == key:
            return self._row
        return None

    def add(self, row):
        self._row = row

    async def commit(self):
        self.commits += 1

    async def delete(self, row):
        self._row = None
        await self.commit()


@pytest.mark.asyncio
async def test_status_no_row():
    svc = TwoFactorService(session=_FakeSession())  # type: ignore[arg-type]
    st = await svc.status(user_id="user-1")
    assert st.enabled is False
    assert st.verified_at is None


@pytest.mark.asyncio
async def test_is_enabled_no_row():
    svc = TwoFactorService(session=_FakeSession())  # type: ignore[arg-type]
    assert await svc.is_enabled(user_id="user-1") is False


@pytest.mark.asyncio
async def test_setup_creates_row_and_returns_qr():
    session = _FakeSession()
    svc = TwoFactorService(session=session)  # type: ignore[arg-type]

    result = await svc.setup(user_id="user-1", email="user@test.sk")
    assert result.secret
    assert len(result.secret) >= 16
    assert "otpauth://" in result.otpauth_uri
    # @ je URL-encoded ako %40 v otpauth URI
    assert "user%40test.sk" in result.otpauth_uri or "user@test.sk" in result.otpauth_uri
    assert "<svg" in result.qr_svg
    assert session.commits >= 1


@pytest.mark.asyncio
async def test_verify_rejects_short_code():
    svc = TwoFactorService(session=_FakeSession())  # type: ignore[arg-type]
    ok, codes = await svc.verify_and_enable(user_id="user-1", code="123")
    assert ok is False
    assert codes == []


@pytest.mark.asyncio
async def test_verify_rejects_wrong_code():
    svc = TwoFactorService(session=_FakeSession())  # type: ignore[arg-type]
    ok, codes = await svc.verify_and_enable(user_id="user-1", code="000000")
    assert ok is False


def test_backup_code_count_constant():
    assert BACKUP_CODE_COUNT == 8


def test_generate_backup_codes_format():
    from app.modules.auth.application.two_factor import _generate_backup_codes

    codes = _generate_backup_codes()
    assert len(codes) == BACKUP_CODE_COUNT
    for c in codes:
        # format XXXX-XXXX
        assert len(c) == 9
        assert c[4] == "-"
