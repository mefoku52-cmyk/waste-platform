"""Audit detail redaction regression tests."""

from app.modules.admin.presentation.router import _redact_details


def test_redacts_sensitive_key_values():
    out = _redact_details(
        "token=abc123; password=hunter2; api_key=xyz; authorization=Bearer secret"
    )
    assert out is not None
    assert "abc123" not in out
    assert "hunter2" not in out
    assert "xyz" not in out
    assert "Bearer" not in out
    assert out.count("[REDACTED]") >= 4


def test_redacts_jwt_and_long_hex():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.signature123"
    hex_value = "a" * 40
    out = _redact_details(f"token={jwt}; hash={hex_value}")
    assert out is not None
    assert jwt not in out
    assert hex_value not in out


def test_keeps_ordinary_details():
    text = "companyId=abc; status=verified"
    assert _redact_details(text) == text


def test_none_and_empty():
    assert _redact_details(None) is None
    assert _redact_details("") == ""
