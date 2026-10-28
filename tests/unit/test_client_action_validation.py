"""Tests for pure functions in client_action_validation."""

from __future__ import annotations

from app.modules.agent_platform.infrastructure.tools.client_action_validation import (
    validate_client_action,
)


def test_unknown_action_rejected() -> None:
    r = validate_client_action("does_not_exist", {})
    assert r.valid is False
    assert r.error_code == "client_unknown_action"


def test_no_arg_actions_valid() -> None:
    for name in (
        "open_new_listing",
        "open_listings_list",
        "open_companies",
        "open_dashboard",
        "open_inquiries",
        "open_new_company",
        "open_documents",
        "open_new_document",
        "open_chat",
        "open_settings",
        "open_admin",
    ):
        r = validate_client_action(name, None)
        assert r.valid is True, name
        assert r.arguments == {}


def test_fill_form_field_valid_and_numeric() -> None:
    r = validate_client_action("fill_form_field", {"field": "title", "value": "hello"})
    assert r.valid is True
    r2 = validate_client_action("fill_form_field", {"field": "price", "value": "12.5"})
    assert r2.valid is True
    r3 = validate_client_action("fill_form_field", {"field": "price", "value": 5})
    assert r3.valid is True


def test_fill_form_field_invalid_field() -> None:
    r = validate_client_action("fill_form_field", {"field": "password", "value": "x"})
    assert r.valid is False
    assert r.error_code == "client_field_not_allowed"


def test_fill_form_field_missing_value() -> None:
    r = validate_client_action("fill_form_field", {"field": "title"})
    assert r.valid is False
    assert r.error_code == "client_missing_value"


def test_fill_form_field_non_scalar() -> None:
    r = validate_client_action("fill_form_field", {"field": "title", "value": {"a": 1}})
    assert r.valid is False
    assert r.error_code == "client_invalid_value"


def test_fill_form_field_bool_numeric_rejected() -> None:
    r = validate_client_action("fill_form_field", {"field": "quantity", "value": True})
    assert r.valid is False


def test_fill_form_field_text_too_long() -> None:
    r = validate_client_action("fill_form_field", {"field": "title", "value": "x" * 2001})
    assert r.valid is False
    assert r.error_code == "client_value_too_long"


def test_highlight_field() -> None:
    assert validate_client_action("highlight_field", {"field": "title"}).valid is True
    assert validate_client_action("highlight_field", {"field": "nope"}).valid is False


def test_show_toast() -> None:
    r = validate_client_action("show_toast", {"message": "hi", "level": "success"})
    assert r.valid is True
    assert r.arguments == {"message": "hi", "level": "success"}
    # default level
    r2 = validate_client_action("show_toast", {"message": "hi"})
    assert r2.valid is True
    assert r2.arguments["level"] == "info"
    # empty
    assert validate_client_action("show_toast", {"message": "   "}).valid is False
    # too long
    assert validate_client_action("show_toast", {"message": "x" * 501}).valid is False
    # bad level
    assert validate_client_action("show_toast", {"message": "hi", "level": "debug"}).valid is False


def test_navigate_valid() -> None:
    r = validate_client_action("navigate", {"url": "/dashboard/companies/123"})
    assert r.valid is True
    assert r.arguments == {"url": "/dashboard/companies/123"}


def test_navigate_rejects_external() -> None:
    for url in ("http://evil.com", "//evil.com", "https://x", "evil.com/path"):
        assert validate_client_action("navigate", {"url": url}).valid is False, url


def test_navigate_rejects_traversal() -> None:
    for url in ("/a/../b", "/a/..", "/a\\b", "/a:b"):
        assert validate_client_action("navigate", {"url": url}).valid is False, url


def test_navigate_rejects_encoded_traversal() -> None:
    # decoded contains '..'
    r = validate_client_action("navigate", {"url": "/a/%2e%2e/b"})
    assert r.valid is False


def test_open_with_id() -> None:
    assert validate_client_action("open_listing", {"listing_id": "abc-123"}).valid is True
    assert validate_client_action("open_listing", {"listing_id": "bad id"}).valid is False
    assert validate_client_action("open_company", {"company_id": "c_1"}).valid is True
    assert validate_client_action("open_company", {}).valid is False
