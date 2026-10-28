"""Tests for pure helper functions in lead_finder services."""

from __future__ import annotations

from app.modules.lead_finder.application.services.email_drafter import (
    _fallback_draft,
    _parse_draft,
)
from app.modules.lead_finder.application.services.email_finder import (
    _email_matches_company,
    _is_free_email,
)


def test_is_free_email_known_providers() -> None:
    for email in ("foo@gmail.com", "bar@yahoo.com", "x@outlook.com"):
        assert _is_free_email(email) is True


def test_is_free_email_company_domain() -> None:
    assert _is_free_email("info@acme.sk") is False


def test_is_free_email_free_tld() -> None:
    assert _is_free_email("x@spam.xyz") is True


def test_is_free_email_invalid() -> None:
    assert _is_free_email("no-at-sign") is True


def test_email_matches_company_true() -> None:
    assert _email_matches_company("info@djservice.sk", "D-J service s.r.o.") is True
    assert _email_matches_company("info@ekol.sk", "EKOL - recyklacne systemy") is True


def test_email_matches_company_false() -> None:
    assert _email_matches_company("support@discord.com", "D-J service s.r.o.") is False


def test_email_matches_company_invalid() -> None:
    assert _email_matches_company("garbage", "Acme s.r.o.") is False


def test_fallback_draft_contains_required_blocks() -> None:
    d = _fallback_draft(company_name="Acme s.r.o.", city="Bratislava", industry="drevo")
    assert "Acme s.r.o." in d.subject
    assert "Bratislava" in d.body
    assert "drevo" in d.body
    assert "STOP" in d.body
    assert "trc-cmep.sk" in d.body


def test_fallback_draft_no_city_industry() -> None:
    d = _fallback_draft(company_name="Foo", early_bird=True)
    assert "Prvých 10 firiem" in d.body


def test_fallback_draft_no_early_bird() -> None:
    d = _fallback_draft(company_name="Foo", early_bird=False)
    assert "Prvých 10 firiem" not in d.body


def test_parse_draft_subject_and_body() -> None:
    text = "SUBJECT: Test\n---\nAhoj svet"
    d = _parse_draft(text, fallback_company="Firma X")
    assert d.subject == "Test"
    assert "Ahoj svet" in d.body


def test_parse_draft_empty_fallback() -> None:
    d = _parse_draft("", fallback_company="Firma X")
    assert "Firma X" in d.subject
    assert "STOP" in d.body
