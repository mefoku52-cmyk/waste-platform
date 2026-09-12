"""Unit tests pre domain exceptions."""

from app.shared.domain.exceptions import (
    DomainError,
    NotFoundDomainError,
    ValidationDomainError,
)


def test_domain_error_is_base():
    """DomainError je základná výnimka."""
    assert issubclass(NotFoundDomainError, DomainError)
    assert issubclass(ValidationDomainError, DomainError)


def test_not_found_creation():
    """NotFoundDomainError sa dá vytvoriť so správou."""
    exc = NotFoundDomainError("User 123 not found")
    assert "User 123" in str(exc)


def test_validation_creation():
    """ValidationDomainError sa dá vytvoriť so správou."""
    exc = ValidationDomainError("Email is invalid")
    assert "Email" in str(exc)


def test_domain_error_inheritance():
    """DomainError je Exception."""
    assert issubclass(DomainError, Exception)
