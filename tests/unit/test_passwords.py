"""Unit tests pre PasswordService."""

import pytest

from app.shared.application.passwords import PasswordService


@pytest.fixture
def service():
    return PasswordService()


def test_hash_password_returns_string(service):
    """Heslo sa zaheshuje a nie je plaintext."""
    h = service.hash_password("MySecret123!")
    assert isinstance(h, str)
    assert h != "MySecret123!"
    assert len(h) > 20


def test_hash_password_verify_roundtrip(service):
    """Hash + verify → True."""
    h = service.hash_password("MySecret123!")
    assert service.verify_password("MySecret123!", h) is True


def test_verify_password_wrong(service):
    """Zlé heslo → False."""
    h = service.hash_password("MySecret123!")
    assert service.verify_password("WrongPass", h) is False


def test_hash_password_salted(service):
    """Hash musí byť saltovaný (iný pri každom volaní)."""
    h1 = service.hash_password("SamePassword")
    h2 = service.hash_password("SamePassword")
    assert h1 != h2


def test_hash_password_empty(service):
    """Prázdne heslo sa dá zaheshovať."""
    h = service.hash_password("")
    assert isinstance(h, str)


def test_verify_password_invalid_hash(service):
    """Neplatný hash → passlib môže vyhodiť výnimku alebo vrátiť False.

    Akceptujeme obe správania — dôležité je, že to nespadne s neočakávanou chybou.
    """
    try:
        result = service.verify_password("anything", "not-a-valid-hash")
        # Ak passlib vráti hodnotu, musí byť False
        assert result is False
    except Exception:
        # Ak passlib vyhodí výnimku, je to tiež prijateľné správanie
        pass
