"""Local file upload API (dev-friendly; later swap to MinIO)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_ROOT = Path("var/uploads")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("")
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

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / name
    dest.write_bytes(data)

    # relative URL served by this API
    url = f"/api/v1/uploads/files/{name}"
    return {
        "url": url,
        "filename": name,
        "originalName": file.filename,
        "size": len(data),
        "contentType": file.content_type,
    }


@router.get("/files/{filename}")
async def get_uploaded_file(filename: str):
    # prevent path traversal
    safe = Path(filename).name
    path = UPLOAD_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
