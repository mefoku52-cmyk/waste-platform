"""Shared local upload storage helpers.

Single source of truth for where uploaded files live, which extensions and
content types are allowed, and how a ``file_id`` is validated. Both the
uploads router and any module that serves stored files (e.g. public company
pages) use these helpers so the rules cannot drift apart.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_DATA_DIR = os.getenv("APP_DATA_DIR", "/var/data")
UPLOAD_ROOT = Path(APP_DATA_DIR) / "uploads"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
ALLOWED_MIME = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BYTES = 8 * 1024 * 1024
CHUNK_BYTES = 64 * 1024

# Magic-byte signatures (prefix) → canonical image kind.
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)


def sanitize_file_id(file_id: str) -> str | None:
    """Return the safe file name, or ``None`` if the id is invalid.

    Struktúra: 32 hex znakov (uuid4 hex) + povolená prípona. Zabráni
    path traversal (``..``/``/``/``\\``), cudzím príponám a inému tvaru.
    """
    if not file_id:
        return None
    safe = Path(file_id).name
    if safe != file_id or ".." in file_id or "/" in file_id or "\\" in file_id:
        return None
    suffix = Path(safe).suffix.lower()
    stem = Path(safe).stem
    if suffix not in ALLOWED_EXT:
        return None
    if len(stem) != 32 or any(c not in "0123456789abcdef" for c in stem.lower()):
        return None
    return safe


def resolve_upload_path(file_id: str) -> Path:
    """Map a validated ``file_id`` to its on-disk path."""
    return UPLOAD_ROOT / file_id


def sniff_image_type(header: bytes) -> str | None:
    """Detect the image kind from the first bytes; ``None`` if not an image.

    WebP is a RIFF container: ``RIFF`` + 4 size bytes + ``WEBP``.
    """
    if header.startswith(_IMAGE_SIGNATURES[0][0]):
        return "jpeg"
    if header.startswith(_IMAGE_SIGNATURES[1][0]):
        return "png"
    if header.startswith(_IMAGE_SIGNATURES[2][0]) or header.startswith(_IMAGE_SIGNATURES[3][0]):
        return "gif"
    if len(header) >= 12 and header[0:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


def content_matches_extension(suffix: str, header: bytes) -> bool:
    """True if the sniffed content matches the file extension.

    Non-image extensions (.pdf) are not content-checked here (kept as-is to
    avoid changing existing PDF behaviour); images must match their bytes.
    """
    ext = suffix.lower()
    if ext not in IMAGE_EXT:
        return True
    kind = sniff_image_type(header)
    if kind is None:
        return False
    return (ext in {".jpg", ".jpeg"} and kind == "jpeg") or ext == f".{kind}"
