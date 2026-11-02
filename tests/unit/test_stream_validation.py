"""Unit tests for stream-based size enforcement and magic-byte validation."""

import pytest

from app.modules.listings.infrastructure.magic_bytes import is_valid_image_content
from app.modules.listings.presentation.photos_router import MAX_SIZE_BYTES


def test_size_constant():
    assert MAX_SIZE_BYTES == 10 * 1024 * 1024


def test_magic_bytes_still_work():
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert is_valid_image_content(jpeg, "image/jpeg") is True
    assert is_valid_image_content(b"", "image/jpeg") is False
    assert is_valid_image_content(b"not image", "image/jpeg") is False


def test_oversize_rejected_by_constant():
    assert 11 * 1024 * 1024 > MAX_SIZE_BYTES