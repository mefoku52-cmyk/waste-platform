"""daily_discover - _usable + konstanty."""

from app.modules.lead_finder.application.services.daily_discover import (
    MAX_DAILY,
    QUERIES,
    SKIP_MARKERS,
    _usable,
)


def test_max_daily_is_35():
    assert MAX_DAILY == 35


def test_queries_not_empty():
    assert len(QUERIES) > 5


def test_queries_are_dicts():
    for q in QUERIES:
        assert isinstance(q, dict)
        assert len(q) > 0


def test_skip_markers_contains_bankruptcy():
    for marker in ["konkurz", "likvidac", "vzniku"]:
        assert marker in SKIP_MARKERS


def test_usable_valid_company():
    row = {"legalName": "Test s.r.o.", "ico": "12345678"}
    assert _usable(row, set()) is True


def test_usable_no_name():
    row = {"legalName": "", "ico": "12345678"}
    assert _usable(row, set()) is False


def test_usable_missing_name():
    row = {"ico": "12345678"}
    assert _usable(row, set()) is False


def test_usable_short_ico():
    row = {"legalName": "Test s.r.o.", "ico": "123"}
    assert _usable(row, set()) is False


def test_usable_missing_ico():
    row = {"legalName": "Test s.r.o."}
    assert _usable(row, set()) is False


def test_usable_known_ico():
    row = {"legalName": "Test s.r.o.", "ico": "12345678"}
    assert _usable(row, {"12345678"}) is False


def test_usable_skip_marker_konkurz():
    row = {"legalName": "Firma v konkurze s.r.o.", "ico": "12345678"}
    assert _usable(row, set()) is False


def test_usable_skip_marker_likvidacia():
    row = {"legalName": "Firma v likvidacii s.r.o.", "ico": "12345678"}
    assert _usable(row, set()) is False


def test_usable_skip_marker_vznik():
    """Slovo 'vzniku' v nazve -> skip (napr. 'Firma pred vznikom')."""
    row = {"legalName": "Firma vo vzniku s.r.o.", "ico": "12345678"}
    assert _usable(row, set()) is False
