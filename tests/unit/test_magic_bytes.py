"""Unit tests for magic-byte image validation."""

from app.modules.listings.infrastructure.magic_bytes import is_valid_image_content


def test_valid_jpeg():
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 10
    assert is_valid_image_content(data, "image/jpeg") is True


def test_valid_png():
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
    assert is_valid_image_content(data, "image/png") is True


def test_valid_webp():
    data = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 10
    assert is_valid_image_content(data, "image/webp") is True


def test_fake_mime():
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 10
    assert is_valid_image_content(data, "image/png") is False


def test_empty():
    assert is_valid_image_content(b"", "image/jpeg") is False


def test_corrupted():
    assert is_valid_image_content(b"not an image", "image/jpeg") is False