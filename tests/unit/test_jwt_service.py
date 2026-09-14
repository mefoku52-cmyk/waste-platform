from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio

from app.shared.infrastructure.security.jwt_exceptions import (
    InvalidTokenError,
    JwtServiceError,
    TokenFamilyRevokedError,
    TokenRevokedError,
    TokenTypeMismatchError,
    TokenUserRevokedError,
)
from app.shared.infrastructure.security.jwt_revocation_store import TokenRevocationStore
from app.shared.infrastructure.security.jwt_service import JwtService


@pytest_asyncio.fixture
async def service():
    store = TokenRevocationStore()
    jwt_service = JwtService(revocation_store=store)
    try:
        yield jwt_service
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_decode_and_validate_access(service):
    token, _ = await service.issue_access_token(subject="user-abc")
    payload = await service.decode_and_validate(token, expected_type="access")
    assert payload["sub"] == "user-abc"


@pytest.mark.asyncio
async def test_issue_refresh_and_validate(service):
    token, *_ = await service.issue_refresh_token(subject="user-abc", family_id=str(uuid4()))
    payload = await service.decode_and_validate(token, expected_type="refresh")
    assert payload["sub"] == "user-abc"


@pytest.mark.asyncio
async def test_access_rejected_as_refresh(service):
    token, _ = await service.issue_access_token(subject="user-abc")
    with pytest.raises((TokenTypeMismatchError, JwtServiceError)):
        await service.decode_and_validate(token, expected_type="refresh")


@pytest.mark.asyncio
async def test_refresh_rejected_as_access(service):
    token, *_ = await service.issue_refresh_token(subject="user-abc", family_id=str(uuid4()))
    with pytest.raises((TokenTypeMismatchError, JwtServiceError)):
        await service.decode_and_validate(token, expected_type="access")


@pytest.mark.asyncio
async def test_garbage_token(service):
    with pytest.raises((InvalidTokenError, JwtServiceError)):
        await service.decode_and_validate("not-a-jwt", expected_type="access")


@pytest.mark.asyncio
async def test_empty_token(service):
    with pytest.raises((InvalidTokenError, JwtServiceError)):
        await service.decode_and_validate("", expected_type="access")


@pytest.mark.asyncio
async def test_sync_decode_roundtrip(service):
    token, _ = await service.issue_access_token(subject="user-xyz")
    payload = service.decode(token)
    assert payload["sub"] == "user-xyz"


@pytest.mark.asyncio
async def test_revoke_access_then_validate_fails(service):
    token, _ = await service.issue_access_token(subject="user-abc")
    payload = await service.decode_and_validate(token, expected_type="access")
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti is None:
        pytest.skip("access token nemá jti")
    exp_dt = (
        datetime.fromtimestamp(exp, tz=UTC)
        if isinstance(exp, (int, float))
        else datetime.now(UTC) + timedelta(hours=1)
    )
    await service.revoke_access_token(jti, exp_dt)
    with pytest.raises((TokenRevokedError, JwtServiceError)):
        await service.decode_and_validate(token, expected_type="access")


@pytest.mark.asyncio
async def test_revoke_refresh_family(service):
    token, *_ = await service.issue_refresh_token(subject="user-abc", family_id=str(uuid4()))
    payload = await service.decode_and_validate(token, expected_type="refresh")
    jti = payload.get("jti")
    family = payload.get("fam") or payload.get("family_id") or payload.get("fid") or "fam-rev"
    exp = payload.get("exp")
    if not jti:
        pytest.skip("refresh token nemá jti")
    exp_dt = (
        datetime.fromtimestamp(exp, tz=UTC)
        if isinstance(exp, (int, float))
        else datetime.now(UTC) + timedelta(hours=1)
    )
    await service.revoke_refresh_token(jti, family, exp_dt)
    with pytest.raises((TokenFamilyRevokedError, TokenRevokedError, JwtServiceError)):
        await service.decode_and_validate(token, expected_type="refresh")


@pytest.mark.asyncio
async def test_revoke_all_user_tokens(service):
    token, _ = await service.issue_access_token(subject="user-abc")
    await service.revoke_all_user_tokens("user-abc")
    with pytest.raises((TokenUserRevokedError, TokenRevokedError, JwtServiceError)):
        await service.decode_and_validate(token, expected_type="access")


@pytest.mark.asyncio
async def test_revocation_store_property(service):
    assert service.revocation_store is not None
