"""Photo management router with repository integration and membership ACL."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.infrastructure.models.listing_photo import ListingPhotoModel
from app.modules.listings.infrastructure.magic_bytes import is_valid_image_content
from app.modules.listings.infrastructure.repositories.listing_photo_repository import (
    ListingPhotoRepository,
)
from app.shared.infrastructure.db.session import get_db_session
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
    content: bytes | None = None  # optional raw bytes for magic-byte check


async def _resolve_listing_company(listing_id: UUID, session: AsyncSession) -> UUID | None:
    """Resolve owning company_id from the listings table (trusted source)."""
    from sqlalchemy import select
    from app.modules.listings.infrastructure.models import ListingsModel

    result = await session.execute(
        select(ListingsModel.company_id).where(ListingsModel.id == listing_id)
    )
    return result.scalar_one_or_none()


@router.post("", status_code=201)
async def add_photo(
    listing_id: UUID,
    payload: PhotoCreateRequest,
    current_user=Depends(require_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    if payload.mime_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Unsupported MIME type")
    if payload.size_bytes > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large")
    if payload.size_bytes <= 0:
        raise HTTPException(status_code=400, detail="Invalid size")

    # Magic-byte validation of actual content (if provided)
    content = getattr(payload, "content", None)
    if content is not None:
        if not is_valid_image_content(content, payload.mime_type):
            raise HTTPException(status_code=400, detail="File content does not match declared MIME type")
        if len(content) > MAX_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File too large")

    company_id = await _resolve_listing_company(listing_id, session)
    if company_id is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Membership ACL – only members of the owning company
    require_company_member(current_user, company_id, action="add photos to")

    photo = ListingPhotoModel(
        id=uuid4(),
        listing_id=listing_id,
        company_id=company_id,
        storage_key=payload.storage_key,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        is_primary=payload.is_primary,
        sort_order=0,
        created_at=datetime.now(UTC),
        created_by=current_user.user.id,
    )
    repo = ListingPhotoRepository(session)
    await repo.add(photo)
    await session.flush()

    return {
        "id": str(photo.id),
        "listing_id": str(listing_id),
        "status": "created",
    }


@router.get("")
async def list_photos(
    listing_id: UUID,
    current_user=Depends(require_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    company_id = await _resolve_listing_company(listing_id, session)
    if company_id is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    require_company_member(current_user, company_id, action="view photos of")

    repo = ListingPhotoRepository(session)
    photos = await repo.list_for_listing(listing_id, company_id)
    return [
        {
            "id": str(p.id),
            "storage_key": p.storage_key,
            "mime_type": p.mime_type,
            "size_bytes": p.size_bytes,
            "is_primary": p.is_primary,
        }
        for p in photos
    ]