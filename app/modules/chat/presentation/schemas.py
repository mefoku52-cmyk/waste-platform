"""chat schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    recipientUserId: UUID
    recipientCompanyId: UUID | None = None
    initiatorCompanyId: UUID | None = None
    listingId: UUID | None = None
    subject: str = Field(min_length=1, max_length=255)


class SendMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class ChatThreadData(BaseModel):
    id: UUID
    listingId: UUID | None
    initiatorUserId: UUID
    initiatorCompanyId: UUID | None
    recipientUserId: UUID
    recipientCompanyId: UUID | None
    subject: str
    status: str
    lastMessageAt: datetime | None
    createdAt: datetime
    updatedAt: datetime


class ChatMessageData(BaseModel):
    id: UUID
    threadId: UUID
    senderUserId: UUID
    senderCompanyId: UUID | None
    body: str
    readAt: datetime | None
    createdAt: datetime


class ChatThreadResponse(BaseModel):
    data: ChatThreadData


class ChatMessageResponse(BaseModel):
    data: ChatMessageData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedThreadsResponse(BaseModel):
    items: list[ChatThreadData]
    meta: PaginationMeta


class PaginatedMessagesResponse(BaseModel):
    items: list[ChatMessageData]
    meta: PaginationMeta


class UnreadCountResponse(BaseModel):
    unread: int
