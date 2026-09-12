"""Unit tests pre User entity."""

from uuid import uuid4

import pytest

from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.shared.domain.exceptions import ValidationDomainError


def _make_user(**overrides):
    """Helper na vytvorenie validného usera."""
    defaults = {
        "id": uuid4(),
        "email": "test@example.com",
        "password_hash": "hashed-password",
        "first_name": "Ján",
        "last_name": "Novák",
        "display_name": None,
        "phone": None,
        "locale": None,
        "timezone": None,
        "last_login_at": None,
        "status": UserStatus.ACTIVE,
    }
    defaults.update(overrides)
    return User(**defaults)


def test_user_valid():
    """Validný user prejde validate()."""
    user = _make_user()
    user.validate()


def test_user_invalid_email():
    """Email bez @ → ValidationDomainError."""
    user = _make_user(email="invalid-email")
    with pytest.raises(ValidationDomainError):
        user.validate()


def test_user_empty_first_name():
    """Prázdne meno → ValidationDomainError."""
    user = _make_user(first_name="")
    with pytest.raises(ValidationDomainError):
        user.validate()


def test_user_empty_last_name():
    """Prázdne priezvisko → ValidationDomainError."""
    user = _make_user(last_name="")
    with pytest.raises(ValidationDomainError):
        user.validate()


def test_user_transition_active_to_suspended():
    """Active → Suspended je povolené."""
    user = _make_user(status=UserStatus.ACTIVE)
    user.transition_status(UserStatus.SUSPENDED)
    assert user.status == UserStatus.SUSPENDED


def test_user_transition_deactivated_to_active_fails():
    """Deactivated → Active je zakázané."""
    from app.shared.domain.exceptions import ValidationDomainError

    user = _make_user(status=UserStatus.DEACTIVATED)
    with pytest.raises((ValidationDomainError, Exception)):
        user.transition_status(UserStatus.ACTIVE)
