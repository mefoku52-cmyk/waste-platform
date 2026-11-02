"""Photo management router (company-scoped)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.modules.listings.domain.photos import ListingPhoto, PhotoACL
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import require_company_member

router = APIRouter(prefix="/listings/{listing_id}/photos", tags=["photos"])


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
    # In full impl resolve company_id from listing and check ACL
    # Placeholder response
    return {"listing_id": str(listing_id), "status": "created"}


@router.get("")
async def list_photos(
    listing_id: UUID,
    current_user=Depends(require_current_user),
):
    # ACL check would happen here against company membership
    return []