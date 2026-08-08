"""analytics API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnalyticsEventCreateRequest(BaseModel):
    eventType: str
    entityType: str
    entityId: UUID | None = None
    companyId: UUID | None = None
    eventMetadata: str | None = None
    recordedAt: datetime


class AnalyticsEventUpdateRequest(BaseModel):
    eventType: str | None = None
    entityType: str | None = None
    entityId: UUID | None = None
    companyId: UUID | None = None
    eventMetadata: str | None = None
    recordedAt: datetime | None = None


class AnalyticsEventData(BaseModel):
    id: UUID
    eventType: str
    entityType: str
    entityId: UUID | None
    companyId: UUID | None
    eventMetadata: str | None
    recordedAt: datetime
    createdAt: datetime
    updatedAt: datetime


class AnalyticsEventResponse(BaseModel):
    data: AnalyticsEventData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedAnalyticsEventsResponse(BaseModel):
    items: list[AnalyticsEventData]
    meta: PaginationMeta
