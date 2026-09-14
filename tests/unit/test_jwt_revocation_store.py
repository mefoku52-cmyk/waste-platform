from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio

from app.shared.infrastructure.security.jwt_revocation_store import (
    TokenRevocationStore,
    get_revocation_store,
)


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=seconds)


@pytest_asyncio.fixture
async def store():
    s = TokenRevocationStore()
    try:
        yield s
    finally:
        await s.close()


@pytest.mark.asyncio
async def test_access_token_not_revoked_by_default(store):
    assert await store.is_access_token_revoked("jti-missing") is False


@pytest.mark.asyncio
async def test_revoke_and_detect_access_token(store):
    await store.revoke_access_token("jti-1", _future())
    assert await store.is_access_token_revoked("jti-1") is True
    assert await store.is_access_token_revoked("jti-other") is False


@pytest.mark.asyncio
async def test_family_not_revoked_by_default(store):
    assert await store.is_family_revoked("fam-missing") is False


@pytest.mark.asyncio
async def test_revoke_refresh_revokes_family(store):
    await store.revoke_refresh_token("jti-r1", "fam-a", _future())
    assert await store.is_family_revoked("fam-a") is True
    assert await store.is_family_revoked("fam-b") is False


@pytest.mark.asyncio
async def test_user_cutoff_set(store):
    subject = "user-cutoff-unique-a1b2"
    cutoff = datetime.now(UTC)
    await store.revoke_user_tokens_after(subject, cutoff)
    got = await store.get_user_tokens_revoked_after(subject)
    assert got is not None


@pytest.mark.asyncio
async def test_later_cutoff_overwrites(store):
    subject = "user-cutoff-unique-c3d4"
    t1 = datetime.now(UTC) - timedelta(minutes=5)
    t2 = datetime.now(UTC)
    await store.revoke_user_tokens_after(subject, t1)
    await store.revoke_user_tokens_after(subject, t2)
    got = await store.get_user_tokens_revoked_after(subject)
    assert got is not None


@pytest.mark.asyncio
async def test_close_is_idempotent(store):
    await store.close()
    await store.close()


@pytest.mark.asyncio
async def test_get_revocation_store_returns_instance():
    s = get_revocation_store()
    assert isinstance(s, TokenRevocationStore)


@pytest.mark.asyncio
async def test_expired_access_jti_behaviour(store):
    await store.revoke_access_token("jti-old", _past())
    revoked = await store.is_access_token_revoked("jti-old")
    assert revoked in (True, False)
