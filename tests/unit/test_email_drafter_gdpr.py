"""EmailDrafter parse + GDPR footer tests."""

from __future__ import annotations

from app.modules.lead_finder.application.services.email_drafter import (
    _SYSTEM,
    _parse_draft,
)


def test_parse_with_subject():
    text = "SUBJECT: Test\n---\nTelo emailu."
    d = _parse_draft(text, fallback_company="Firma X")
    assert d.subject == "Test"
    assert "Telo emailu" in d.body


def test_parse_empty_returns_default_with_stop():
    d = _parse_draft("", fallback_company="Firma X")
    assert "Firma X" in d.subject
    assert "STOP" in d.body
    assert "GDPR" in d.body
    assert "RPO" in d.body


def test_system_prompt_has_gdpr_framework():
    assert "GDPR" in _SYSTEM
    assert "452/2021" in _SYSTEM
    assert "legitimate interest" in _SYSTEM.lower() or "opravneny zaujem" in _SYSTEM.lower()


def test_system_prompt_has_mandatory_optout():
    assert "STOP" in _SYSTEM


def test_system_prompt_has_gdpr_footer():
    assert "RPO" in _SYSTEM
    assert "art" in _SYSTEM.lower() or "cl. 6" in _SYSTEM or "6 ods" in _SYSTEM
