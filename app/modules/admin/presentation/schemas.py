"""admin API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AdminAuditEntryCreateRequest(BaseModel):
    actorUserId: UUID
    action: str
    targetType: str
    targetId: UUID | None = None
    details: str | None = None


class AdminAuditEntryUpdateRequest(BaseModel):
    actorUserId: UUID | None = None
    action: str | None = None
    targetType: str | None = None
    targetId: UUID | None = None
    details: str | None = None
    status: str | None = None


class AdminAuditEntryData(BaseModel):
    id: UUID
    actorUserId: UUID
    action: str
    targetType: str
    targetId: UUID | None
    details: str | None
    status: str
    createdAt: datetime
    updatedAt: datetime


class AdminAuditEntryResponse(BaseModel):
    data: AdminAuditEntryData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedAdminAuditEntrysResponse(BaseModel):
    items: list[AdminAuditEntryData]
    meta: PaginationMeta
