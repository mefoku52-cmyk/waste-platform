"""EmailDrafter tests – parse draft, keep unsubscribe, never invent."""

from __future__ import annotations

from app.modules.lead_finder.application.services.email_drafter import (
    _parse_draft,
)


def test_parse_draft_with_subject_and_body() -> None:
    text = "SUBJECT: Test\n---\nAhoj svet"
    d = _parse_draft(text, fallback_company="Firma X")
    assert d.subject == "Test"
    assert "Ahoj svet" in d.body


def test_parse_draft_without_subject_uses_fallback() -> None:
    text = "Dobrý deň, toto je telo."
    d = _parse_draft(text, fallback_company="Firma X")
    assert "Firma X" in d.subject
    assert "Dobrý deň" in d.body


def test_parse_draft_empty_returns_safe_default() -> None:
    d = _parse_draft("", fallback_company="Firma X")
    assert "Firma X" in d.subject
    assert "STOP" in d.body
    assert "trc-cmep.sk" in d.body


def test_parse_draft_keeps_unsubscribe_if_present() -> None:
    text = (
        "SUBJECT: Pozvánka\n---\n"
        "Dobrý deň,\n\n"
        "chceme Vás pozvať na CMEP.\n"
        "Ak nemáte záujem, odpovedzte prosím slovom STOP.\n"
    )
    d = _parse_draft(text, fallback_company="Firma X")
    assert "STOP" in d.body
