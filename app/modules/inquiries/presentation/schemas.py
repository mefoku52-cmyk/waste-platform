"""inquiries API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InquiryCreateRequest(BaseModel):
    listingId: UUID
    companyId: UUID
    message: str
    contactEmail: str
    contactPhone: str | None = None


class InquiryUpdateRequest(BaseModel):
    listingId: UUID | None = None
    companyId: UUID | None = None
    message: str | None = None
    contactEmail: str | None = None
    contactPhone: str | None = None
    status: str | None = None


class InquiryStatusUpdateRequest(BaseModel):
    status: str  # open | answered | closed


class InquiryData(BaseModel):
    id: UUID
    listingId: UUID
    companyId: UUID
    message: str
    contactEmail: str
    contactPhone: str | None
    status: str
    createdAt: datetime
    updatedAt: datetime
    listingTitle: str | None = None


class InquiryResponse(BaseModel):
    data: InquiryData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedInquiriesResponse(BaseModel):
    items: list[InquiryData]
    meta: PaginationMeta
