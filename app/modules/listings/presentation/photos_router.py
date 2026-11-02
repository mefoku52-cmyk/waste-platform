"""Photo management router with MIME and size checks."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_member

router = APIRouter(prefix="/listings/{listing_id}/photos", tags=["photos"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class PhotoCreateRequest(BaseModel):
    storage_key: str
    mime_type: str
    size_bytes: int
    is_primary: bool = False


@router.post("", status_code=201)
async def add_photo(
    listing_id: UUID,
    payload: PhotoCreateRequest,
    current_user=Depends(require_current_user),
):
    if payload.mime_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Unsupported MIME type")
    if payload.size_bytes > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large")
    if payload.size_bytes <= 0:
        raise HTTPException(status_code=400, detail="Invalid size")

    # In full impl: resolve company from listing, check ACL, persist via repository
    return {
        "listing_id": str(listing_id),
        "status": "accepted",
        "mime_type": payload.mime_type,
        "size_bytes": payload.size_bytes,
    }


@router.get("")
async def list_photos(
    listing_id: UUID,
    current_user=Depends(require_current_user),
):
    return []