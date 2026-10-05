"""Testy pre auto-approve service."""

from __future__ import annotations

import pytest

from app.modules.lead_finder.application.services.auto_approve import (
    _is_approvable,
)


@pytest.mark.parametrize(
    "email,expected_ok",
    [
        ("info@firma.sk", True),
        ("kontakt@firma.sk", True),
        ("obchod@firma.sk", True),
        ("noreply@firma.sk", False),
        ("no-reply@firma.sk", False),
        ("postmaster@firma.sk", False),
        ("abuse@firma.sk", False),
        ("webmaster@firma.sk", False),
        ("hostmaster@firma.sk", False),
        ("", False),
        (None, False),
        ("invalid", False),
        ("bez-zavinaca", False),
    ],
)
def test_is_approvable(email, expected_ok):
    """Over ze _is_approvable spravne klasifikuje emaily."""
    ok, _reason = _is_approvable(email)
    assert ok is expected_ok


def test_is_approvable_returns_reason_for_junk():
    """Reason obsahuje typ problemu."""
    ok, reason = _is_approvable("noreply@firma.sk")
    assert ok is False
    assert "junk" in reason


def test_is_approvable_returns_reason_no_email():
    ok, reason = _is_approvable(None)
    assert ok is False
    assert reason == "no_email"


def test_is_approvable_returns_reason_invalid():
    ok, reason = _is_approvable("no-at-sign")
    assert ok is False
    assert reason == "invalid_email"
