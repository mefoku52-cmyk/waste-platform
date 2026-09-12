"""Unit tests pre RefreshSession entity."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.auth.domain.entities import RefreshSession


def test_refresh_session_creation():
    """RefreshSession sa vytvorí so správnymi defaultmi."""
    session = RefreshSession(
        id=uuid4(),
        user_id=uuid4(),
        family_id="family-123",
        jti="jti-456",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    assert session.revoked_at is None
    assert session.reuse_detected_at is None
    assert session.created_at <= datetime.now(UTC)
    assert session.updated_at <= datetime.now(UTC)


def test_refresh_session_with_revocation():
    """RefreshSession s revokáciou."""
    now = datetime.now(UTC)
    session = RefreshSession(
        id=uuid4(),
        user_id=uuid4(),
        family_id="family-789",
        jti="jti-abc",
        expires_at=now + timedelta(days=7),
        revoked_at=now,
    )
    assert session.revoked_at == now
