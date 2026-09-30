"""Chat sanitize — verifies phone/email hiding and reveal toggle."""

from __future__ import annotations

from app.modules.chat.application.services import _sanitize


def test_sanitize_hides_phone():
    text = "Zavolaj mi na +421 910 123 456 prosím."
    out = _sanitize(text, allow_contacts=False)
    assert "910" not in out
    assert "telefon" in out.lower()


def test_sanitize_hides_email():
    text = "Môj email je jan@firma.sk."
    out = _sanitize(text, allow_contacts=False)
    assert "jan@firma.sk" not in out
    assert "email" in out.lower()


def test_sanitize_allows_when_revealed():
    text = "Zavolaj mi na +421 910 123 456 alebo jan@firma.sk."
    out = _sanitize(text, allow_contacts=True)
    assert "+421 910 123 456" in out
    assert "jan@firma.sk" in out


def test_sanitize_empty_string():
    assert _sanitize("", allow_contacts=False) == ""
    assert _sanitize("", allow_contacts=True) == ""


def test_sanitize_keeps_plain_text():
    text = "Dobrý deň, mám záujem o vašu ponuku."
    assert _sanitize(text, allow_contacts=False) == text
