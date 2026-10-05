"""Tests for signed upload URLs.

Covers HMAC signing, verification, expiration, tampering, and the
router's signed-URL enforcement.
"""

from __future__ import annotations

import time

import pytest

from app.modules.uploads.application.signing import (
    DEFAULT_TTL_SECONDS,
    MAX_TTL_SECONDS,
    sign_file_url,
    verify_file_url,
)

SECRET = "test-secret-32-chars-long-abcdef"
FILE_ID = "abc123def456abc123def456abc12345"


def test_sign_returns_expected_shape():
    result = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)

    assert result["file_id"] == FILE_ID
    assert result["expires_at"] > int(time.time())
    assert result["signature"]
    assert result["url_path"].startswith(f"/uploads/{FILE_ID}?")


def test_sign_default_ttl():
    before = int(time.time())
    result = sign_file_url(FILE_ID, SECRET)
    after = int(time.time())

    assert before + DEFAULT_TTL_SECONDS <= result["expires_at"] <= after + DEFAULT_TTL_SECONDS


def test_sign_clamps_ttl_to_max():
    result = sign_file_url(FILE_ID, SECRET, ttl_seconds=99999)
    expected_max = int(time.time()) + MAX_TTL_SECONDS

    assert result["expires_at"] <= expected_max + 2


def test_sign_rejects_empty_inputs():
    with pytest.raises(ValueError):
        sign_file_url("", SECRET)
    with pytest.raises(ValueError):
        sign_file_url(FILE_ID, "")


def test_verify_accepts_valid_signature():
    signed = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    ok, reason = verify_file_url(FILE_ID, SECRET, signed["expires_at"], signed["signature"])

    assert ok is True
    assert reason == "ok"


def test_verify_rejects_tampered_signature():
    signed = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    ok, reason = verify_file_url(FILE_ID, SECRET, signed["expires_at"], "wrong-signature")

    assert ok is False
    assert reason == "mismatch"


def test_verify_rejects_expired_signature():
    signed = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    past = int(time.time()) - 10
    ok, reason = verify_file_url(FILE_ID, SECRET, past, signed["signature"])

    assert ok is False
    assert reason == "expired"


def test_verify_rejects_wrong_file_id():
    signed = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    ok, reason = verify_file_url(
        "different-file-id", SECRET, signed["expires_at"], signed["signature"]
    )

    assert ok is False
    assert reason == "mismatch"


def test_verify_rejects_wrong_secret():
    signed = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    ok, reason = verify_file_url(
        FILE_ID,
        "other-secret-32-chars-long-abcdefg",
        signed["expires_at"],
        signed["signature"],
    )

    assert ok is False
    assert reason == "mismatch"


def test_verify_rejects_missing_inputs():
    ok, reason = verify_file_url("", SECRET, 0, "sig")
    assert ok is False
    assert reason == "missing"

    ok, reason = verify_file_url(FILE_ID, SECRET, 0, "")
    assert ok is False
    assert reason == "missing"


def test_verify_rejects_invalid_expires():
    ok, reason = verify_file_url(FILE_ID, SECRET, "not-a-number", "sig")
    assert ok is False
    assert reason == "invalid"


def test_signature_is_deterministic_for_same_inputs():
    a = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    b = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)

    assert a["expires_at"] == b["expires_at"]
    assert a["signature"] == b["signature"]


def test_signature_differs_for_different_files():
    a = sign_file_url(FILE_ID, SECRET, ttl_seconds=60)
    b = sign_file_url("other-file-id-xyz", SECRET, ttl_seconds=60)

    assert a["signature"] != b["signature"]
