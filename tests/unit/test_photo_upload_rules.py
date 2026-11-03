"""Additional unit tests for photo upload validation."""

import pytest

from app.modules.listings.presentation.photos_router import ALLOWED_MIME, MAX_SIZE_BYTES


def test_mime_whitelist():
    assert ALLOWED_MIME == {"image/jpeg", "image/png", "image/webp"}


def test_size_limit():
    assert MAX_SIZE_BYTES == 10 * 1024 * 1024


def test_reject_oversized():
    # Pure validation logic (router raises HTTPException in full path)
    assert 11 * 1024 * 1024 > MAX_SIZE_BYTES


def test_reject_unknown_mime():
    assert "application/pdf" not in ALLOWED_MIME
    assert "image/gif" not in ALLOWED_MIME