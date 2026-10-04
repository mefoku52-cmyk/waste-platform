"""email_finder - _is_free_email, _email_matches_company, _filter_emails."""

import pytest

from app.modules.lead_finder.application.services.email_finder import (
    _FREE_EMAIL_DOMAINS,
    LegalEmailFinder,
    _email_matches_company,
    _is_free_email,
)


@pytest.mark.parametrize(
    "email",
    [
        "user@gmail.com",
        "user@yahoo.com",
        "user@hotmail.com",
        "user@outlook.com",
        "user@protonmail.com",
        "user@icloud.com",
        "user@centrum.sk",
        "user@azet.sk",
        "user@zoznam.sk",
        "user@seznam.cz",
        "user@wp.pl",
    ],
)
def test_is_free_email_true(email):
    assert _is_free_email(email) is True


@pytest.mark.parametrize(
    "email",
    [
        "info@firma.sk",
        "kontakt@firma.sk",
        "obchod@recyklacia.sk",
        "predaj@ekol.sk",
    ],
)
def test_is_free_email_false(email):
    assert _is_free_email(email) is False


def test_is_free_email_malformed():
    assert _is_free_email("no-at-sign") is True
    assert _is_free_email("") is True


def test_email_matches_company_basic():
    assert _email_matches_company("info@djservice.sk", "D-J service s.r.o.")
    assert _email_matches_company("kontakt@ekol.sk", "EKOL - recyklacne systemy")
    assert _email_matches_company("info@drevosk.sk", "DrevoSK s.r.o.")


def test_email_does_not_match_company():
    assert not _email_matches_company("support@discord.com", "D-J service s.r.o.")
    assert not _email_matches_company("info@google.com", "EKOL")
    assert not _email_matches_company("x@facebook.com", "Recyklacia SK")


def test_email_matches_company_empty_name():
    assert _email_matches_company("info@firma.sk", "") is False


def test_email_matches_company_no_words():
    """Kratke slova (<3 znaky) sa ignoruju."""
    assert _email_matches_company("info@ab.sk", "a s") is False


def test_email_matches_company_malformed():
    assert _email_matches_company("no-at-sign", "Firma") is False


def test_filter_emails_removes_free_providers():
    emails = ["user@gmail.com", "info@firma.sk", "kontakt@firma.sk"]
    result = LegalEmailFinder._filter_emails(emails, "Firma s.r.o.")
    assert "user@gmail.com" not in result
    assert "info@firma.sk" in result


def test_filter_emails_removes_unrelated():
    emails = ["support@discord.com", "info@djservice.sk"]
    result = LegalEmailFinder._filter_emails(emails, "D-J service s.r.o.")
    assert "support@discord.com" not in result
    assert "info@djservice.sk" in result


def test_filter_emails_empty():
    assert LegalEmailFinder._filter_emails([], "Firma") == []


def test_filter_emails_no_company_name():
    """Bez company_name ostavaju len non-free emaily."""
    emails = ["user@gmail.com", "info@firma.sk"]
    result = LegalEmailFinder._filter_emails(emails, None)
    assert "user@gmail.com" not in result
    assert "info@firma.sk" in result


# ---------------------------------------------------------------------------
# Free TLDs (_FREE_TLDS) — suffixova zhoda, nie presna
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email",
    [
        "info@ralenplus.sbs",
        "kontakt@mail.tk",
        "predaj@firma.xyz",
        "obchod@nieco.top",
        "info@klik.click",
        "a@b.icu",
        "a@b.cf",
        "a@b.ml",
        "a@b.ga",
        "a@b.gq",
        "a@firma.work",
        "a@firma.online",
    ],
)
def test_is_free_email_true_for_free_tlds(email):
    assert _is_free_email(email) is True


def test_is_free_email_tld_is_suffix_not_substring():
    """'.sbs' je TLD — nesmie blokovat domenu ktora ho obsahuje uprostred."""
    assert _is_free_email("info@sbsfirma.sk") is False
    assert _is_free_email("info@firma.xyzsk.sk") is False


def test_is_free_email_case_insensitive_tld():
    assert _is_free_email("info@firma.XYZ") is True


def test_is_free_email_empty_domain():
    assert _is_free_email("user@") is True


def test_filter_emails_removes_free_tlds():
    emails = ["info@ralenplus.sbs", "kontakt@mail.tk", "info@firma.sk"]
    result = LegalEmailFinder._filter_emails(emails, "Firma s.r.o.")
    assert "info@ralenplus.sbs" not in result
    assert "kontakt@mail.tk" not in result
    assert "info@firma.sk" in result


# ---------------------------------------------------------------------------
# D2 rule — free provider + local-part match na nazov firmy
# ---------------------------------------------------------------------------


def test_gmail_rejected_when_local_part_does_not_match():
    """ralenplus.sbs@gmail.com pre firmu ODPADY TATRY -> reject."""
    emails = ["ralenplus.sbs@gmail.com"]
    result = LegalEmailFinder._filter_emails(emails, "ODPADY TATRY")
    assert result == []


@pytest.mark.xfail(
    reason="D2 nie je implementovana: _filter_emails zahodí KAŽDÝ free provider "
    "ešte pred kontrolou local-partu. Viď report KROK A.",
    strict=True,
)
def test_gmail_accepted_when_local_part_matches_company():
    """D2: odpadytatry@gmail.com pre firmu ODPADY TATRY -> accept."""
    emails = ["odpadytatry@gmail.com"]
    result = LegalEmailFinder._filter_emails(emails, "ODPADY TATRY")
    assert result == ["odpadytatry@gmail.com"]


def test_free_domains_contains_core():
    assert "gmail.com" in _FREE_EMAIL_DOMAINS
    assert "yahoo.com" in _FREE_EMAIL_DOMAINS
    assert "centrum.sk" in _FREE_EMAIL_DOMAINS


def test_extract_from_html_finds_emails():
    html = "<html>Kontakt: info@firma.sk alebo predaj@firma.sk</html>"
    result = LegalEmailFinder._extract_from_html(html)
    assert "info@firma.sk" in result
    assert "predaj@firma.sk" in result


def test_extract_from_html_mailto():
    html = '<a href="mailto:obchod@firma.sk">Kontakt</a>'
    result = LegalEmailFinder._extract_from_html(html)
    assert "obchod@firma.sk" in result


def test_extract_filters_junk():
    html = "info@firma.sk noreply@firma.sk test@example.com"
    result = LegalEmailFinder._extract_from_html(html)
    assert "info@firma.sk" in result
    assert "noreply@firma.sk" not in result
    assert "test@example.com" not in result


def test_pick_best_prefers_generic():
    result = LegalEmailFinder._pick_best(["jan@firma.sk", "info@firma.sk"])
    assert result == "info@firma.sk"


def test_pick_best_empty():
    assert LegalEmailFinder._pick_best([]) is None


def test_pick_best_fallback_first():
    result = LegalEmailFinder._pick_best(["jan@firma.sk", "peter@firma.sk"])
    assert result == "jan@firma.sk"


def test_find_email_none_url():
    finder = LegalEmailFinder()
    assert finder.find_email_for_company(None) is None
    assert finder.find_email_for_company("") is None
    finder.close()
