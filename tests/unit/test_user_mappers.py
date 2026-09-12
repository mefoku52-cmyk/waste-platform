"""Unit tests pre users application mappers."""

from datetime import UTC, datetime
from uuid import uuid4

from app.modules.users.application.mappers import to_user_dto
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus


def _make_user(**overrides):
    defaults = {
        "id": uuid4(),
        "email": "test@example.com",
        "password_hash": "hashed",
        "first_name": "Ján",
        "last_name": "Novák",
        "display_name": "jano",
        "phone": "+421900000000",
        "locale": "sk",
        "timezone": "Europe/Bratislava",
        "last_login_at": None,
        "status": UserStatus.ACTIVE,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return User(**defaults)


def test_to_user_dto_maps_all_fields():
    """to_user_dto prenesie všetky polia."""
    user = _make_user()
    dto = to_user_dto(user)

    assert dto.id == user.id
    assert dto.email == user.email
    assert dto.first_name == user.first_name
    assert dto.last_name == user.last_name
    assert dto.display_name == user.display_name
    assert dto.phone == user.phone
    assert dto.locale == user.locale
    assert dto.timezone == user.timezone


def test_to_user_dto_status_is_string():
    """to_user_dto konvertuje status na string."""
    user = _make_user(status=UserStatus.SUSPENDED)
    dto = to_user_dto(user)
    assert dto.status == "suspended"


def test_to_user_dto_handles_none_fields():
    """to_user_dto funguje s None hodnotami."""
    user = _make_user(display_name=None, phone=None, locale=None, timezone=None)
    dto = to_user_dto(user)
    assert dto.display_name is None
    assert dto.phone is None
    assert dto.locale is None
    assert dto.timezone is None
