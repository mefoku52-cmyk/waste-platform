"""Unit tests pre JwtService."""

from datetime import UTC, datetime
from uuid import uuid4

import jwt
import pytest

from app.shared.infrastructure.security.jwt_service import JwtService


@pytest.fixture
def service():
    return JwtService()


@pytest.mark.asyncio
async def test_issue_access_token(service):
    """Access token sa vydá a má správny formát."""
    token, expires_at = await service.issue_access_token(subject="user-123")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3
    assert expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_decode_access_token(service):
    """Decode vráti správny payload."""
    token, _ = await service.issue_access_token(subject="user-456")
    payload = service.decode(token)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_issue_refresh_token(service):
    """Refresh token sa vydá s family_id a jti."""
    family_id = str(uuid4())
    token, jti, expires_at = await service.issue_refresh_token(
        subject="user-789",
        family_id=family_id,
    )
    assert isinstance(token, str)
    assert isinstance(jti, str)
    assert expires_at > datetime.now(UTC)

    payload = service.decode(token)
    assert payload["sub"] == "user-789"
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti
    assert payload["family_id"] == family_id


def test_decode_invalid_token(service):
    """Neplatný token → jwt.exceptions.InvalidTokenError."""
    with pytest.raises(jwt.exceptions.InvalidTokenError):
        service.decode("not.a.token")


def test_decode_wrong_signature(service):
    """Token s iným kľúčom → InvalidTokenError."""
    fake = jwt.encode({"sub": "user"}, "wrong-key", algorithm="HS256")
    with pytest.raises(jwt.exceptions.InvalidTokenError):
        service.decode(fake)


@pytest.mark.asyncio
async def test_decode_and_validate_access(service):
    """decode_and_validate pre access token vráti payload."""
    token, _ = await service.issue_access_token(subject="user-abc")
    payload = await service.decode_and_validate(token, expected_type="access")
    assert payload["sub"] == "user-abc"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_decode_and_validate_wrong_type(service):
    """decode_and_validate s nesprávnym typom → výnimka."""
    from app.shared.infrastructure.security.jwt_exceptions import TokenTypeMismatchError

    token, _ = await service.issue_access_token(subject="user-xyz")
    with pytest.raises((TokenTypeMismatchError, Exception)):
        await service.decode_and_validate(token, expected_type="refresh")
