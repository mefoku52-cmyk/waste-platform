"""notifications API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationCreateRequest(BaseModel):
    userId: UUID
    type: str
    title: str
    message: str
    isRead: bool
    relatedEntityId: UUID | None = None


class NotificationUpdateRequest(BaseModel):
    userId: UUID | None = None
    type: str | None = None
    title: str | None = None
    message: str | None = None
    isRead: bool | None = None
    relatedEntityId: UUID | None = None


class NotificationData(BaseModel):
    id: UUID
    userId: UUID
    type: str
    title: str
    message: str
    isRead: bool
    relatedEntityId: UUID | None
    createdAt: datetime
    updatedAt: datetime


class NotificationResponse(BaseModel):
    data: NotificationData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationData]
    meta: PaginationMeta
