"""LegalEmailFinder — HTML extraction tests (no network)."""

from __future__ import annotations

from app.modules.lead_finder.application.services.email_finder import (
    _EMAIL_RE,
    _GENERIC_PREFIXES,
    _JUNK_PATTERNS,
    LegalEmailFinder,
)


def test_email_regex_basic():
    matches = _EMAIL_RE.findall("Kontakt: info@firma.sk a podpora@firma.sk")
    assert "info@firma.sk" in matches
    assert "podpora@firma.sk" in matches


def test_extract_from_html_basic():
    html = "<html><body>Napíšte nám na info@firma.sk</body></html>"
    result = LegalEmailFinder._extract_from_html(html)
    assert "info@firma.sk" in result


def test_extract_from_html_mailto():
    html = '<a href="mailto:obchod@firma.sk">Kontakt</a>'
    result = LegalEmailFinder._extract_from_html(html)
    assert "obchod@firma.sk" in result


def test_extract_filters_junk():
    html = "Píšte na info@firma.sk, nie na no-reply@firma.sk ani test@example.com"
    result = LegalEmailFinder._extract_from_html(html)
    assert "info@firma.sk" in result
    assert "no-reply@firma.sk" not in result
    assert "test@example.com" not in result


def test_pick_best_prefers_generic():
    result = LegalEmailFinder._pick_best(["jan@firma.sk", "info@firma.sk"])
    assert result == "info@firma.sk"


def test_pick_best_returns_first_if_no_generic():
    result = LegalEmailFinder._pick_best(["jan@firma.sk", "peter@firma.sk"])
    assert result == "jan@firma.sk"


def test_pick_best_empty():
    assert LegalEmailFinder._pick_best([]) is None


def test_find_email_none_url_returns_none():
    finder = LegalEmailFinder()
    assert finder.find_email_for_company(None) is None
    assert finder.find_email_for_company("") is None
    finder.close()


def test_junk_patterns_nonempty():
    assert len(_JUNK_PATTERNS) > 0
    assert len(_GENERIC_PREFIXES) > 0
