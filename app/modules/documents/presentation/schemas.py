"""documents API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.documents.domain.enums import DocumentStatus


class DocumentCreateRequest(BaseModel):
    title: str
    documentType: str
    fileUrl: str
    companyId: UUID
    listingId: UUID | None = None


class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    documentType: str | None = None
    fileUrl: str | None = None
    companyId: UUID | None = None
    listingId: UUID | None = None
    status: DocumentStatus | None = None


class DocumentData(BaseModel):
    id: UUID
    title: str
    documentType: str
    fileUrl: str
    companyId: UUID
    listingId: UUID | None
    status: DocumentStatus
    createdAt: datetime
    updatedAt: datetime


class DocumentResponse(BaseModel):
    data: DocumentData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedDocumentsResponse(BaseModel):
    items: list[DocumentData]
    meta: PaginationMeta
