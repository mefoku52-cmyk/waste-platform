"""Multi-photo support for listings with ordering and primary flag."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ListingPhoto(BaseModel):
    id: UUID
    listing_id: UUID
    storage_key: str
    mime_type: str
    size_bytes: int
    is_primary: bool = False
    sort_order: int = 0
    created_at: datetime
    created_by: UUID


class DocumentVersion(BaseModel):
    id: UUID
    document_id: UUID
    version: int
    storage_key: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    created_by: UUID
    change_note: str | None = None


class PhotoService:
    """Placeholder service; full impl would enforce ACL, size and MIME checks."""

    def __init__(self) -> None:
        self._photos: dict[UUID, list[ListingPhoto]] = {}

    def add_photo(self, photo: ListingPhoto) -> None:
        self._photos.setdefault(photo.listing_id, []).append(photo)
        # Ensure only one primary
        if photo.is_primary:
            for p in self._photos[photo.listing_id]:
                if p.id != photo.id:
                    p.is_primary = False