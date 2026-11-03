"""Magic-byte verification for uploaded images."""

from __future__ import annotations

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
WEBP_MAGIC = b"RIFF"


def is_valid_image_content(data: bytes, declared_mime: str) -> bool:
    """Return True only if the first bytes match the declared MIME type."""
    if not data:
        return False
    if declared_mime == "image/jpeg":
        return data.startswith(JPEG_MAGIC)
    if declared_mime == "image/png":
        return data.startswith(PNG_MAGIC)
    if declared_mime == "image/webp":
        return data.startswith(WEBP_MAGIC) and b"WEBP" in data[:16]
    return False