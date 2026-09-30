"""Email domain validator — reject fake/placeholder domains."""

import pytest

from app.shared.application.email_domain_validator import (
    is_fake_email,
    validate_email_domain,
)


@pytest.mark.parametrize(
    "email",
    [
        "user@gmail.com",
        "info@firma.sk",
        "kontakt@realdomena.com",
        "a@b.cz",
        "admin@trc-cmep.sk",
    ],
)
def test_real_email_not_fake(email):
    assert is_fake_email(email) is False


@pytest.mark.parametrize(
    "email",
    [
        "fake@b.c",
        "user@b.test",
        "x@b.invalid",
        "a@b.local",
        "y@b.localhost",
        "z@b.onion",
        "test@example.com",
        "test@example.org",
        "test@example.net",
    ],
)
def test_fake_email_detected(email):
    assert is_fake_email(email) is True


def test_email_without_at_is_fake():
    assert is_fake_email("not-an-email") is True


def test_email_without_dot_in_domain_is_fake():
    assert is_fake_email("user@firma") is True


def test_empty_email_is_fake():
    assert is_fake_email("") is True


def test_validate_email_domain_returns_email():
    assert validate_email_domain("info@firma.sk") == "info@firma.sk"


def test_validate_email_domain_raises_for_fake():
    with pytest.raises(ValueError):
        validate_email_domain("fake@b.c")


def test_case_insensitive_domain():
    assert is_fake_email("user@EXAMPLE.COM") is True
    assert is_fake_email("user@B.C") is True
