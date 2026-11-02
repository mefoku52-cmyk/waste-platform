"""Multi-photo and document versioning with ACL.

Company-scoped. Only members of the owning company can read/write.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class PhotoAccess(str, Enum):
    OWNER = "owner"
    COMPANY_MEMBER = "company_member"
    NONE = "none"


class ListingPhoto(BaseModel):
    id: UUID
    listing_id: UUID
    company_id: UUID
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
    company_id: UUID
    version: int
    storage_key: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    created_by: UUID
    change_note: str | None = None


class PhotoACL:
    """Simple company-scoped ACL."""

    @staticmethod
    def can_read(user_company_ids: set[UUID], photo: ListingPhoto) -> bool:
        return photo.company_id in user_company_ids

    @staticmethod
    def can_write(user_company_ids: set[UUID], photo: ListingPhoto) -> bool:
        return photo.company_id in user_company_ids