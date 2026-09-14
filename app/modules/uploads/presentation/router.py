"""Local file upload API (dev-friendly; later swap to MinIO)."""

from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

from .schemas import UploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_ROOT = Path("var/uploads")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
ALLOWED_MIME = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB


def _validate_file_id(file_id: str) -> str:
    safe = Path(file_id).name
    if safe != file_id or ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(status_code=400, detail="Invalid file id")

    suffix = Path(safe).suffix.lower()
    stem = Path(safe).stem
    if suffix not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if len(stem) != 32 or any(c not in "0123456789abcdef" for c in stem.lower()):
        raise HTTPException(status_code=400, detail="Invalid file id format")
    return safe


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(400, 401, 403, 422, 500),
)
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(require_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type {suffix}. Allowed: {sorted(ALLOWED_EXT)}",
        )

    if file.content_type:
        allowed_for_ext = ALLOWED_MIME.get(suffix, set())
        if allowed_for_ext and file.content_type not in allowed_for_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Content type {file.content_type} does not match extension {suffix}",
            )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    file_id = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / file_id
    dest.write_bytes(data)

    return UploadResponse(
        fileId=file_id,
        url=f"/api/v1/uploads/{file_id}",
        originalName=file.filename,
        size=len(data),
        contentType=file.content_type,
    )


@router.get(
    "/{file_id}",
    responses=error_responses(400, 404, 500),
)
async def get_uploaded_file(file_id: str):
    safe = _validate_file_id(file_id)
    path = UPLOAD_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(path))
    filename = path.name

    response = FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
        filename=filename,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, max-age=3600"
    response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response


@router.get(
    "/files/{file_id}",
    include_in_schema=False,
)
async def get_uploaded_file_legacy(file_id: str):
    return await get_uploaded_file(file_id=file_id)
