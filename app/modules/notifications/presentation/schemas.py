"""notifications API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreateRequest(BaseModel):
    userId: UUID
    type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    isRead: bool = False
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
