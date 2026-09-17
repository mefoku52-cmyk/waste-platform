"""Unit tests for chat sanitize helper."""

from app.modules.chat.application.services import _sanitize


def test_sanitize_plain_text():
    assert _sanitize("Ahoj svet") == "Ahoj svet"


def test_sanitize_removes_email():
    out = _sanitize("Kontaktuj ma na peter@example.com")
    assert "peter@example.com" not in out
    assert "[email skryty]" in out


def test_sanitize_removes_phone():
    out = _sanitize("Zavolaj mi na +421 901 234 567")
    assert "901" not in out
    assert "[telefon skryty]" in out


def test_sanitize_removes_both():
    out = _sanitize("mail: x@y.sk, tel: 0900123456")
    assert "x@y.sk" not in out
    assert "0900123456" not in out
    assert "[email skryty]" in out
    assert "[telefon skryty]" in out


def test_sanitize_keeps_short_numbers():
    assert _sanitize("mam 5 kg") == "mam 5 kg"
