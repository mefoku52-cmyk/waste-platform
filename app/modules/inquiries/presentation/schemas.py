"""inquiries API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.modules.inquiries.domain.enums import InquiryStatus


class InquiryCreateRequest(BaseModel):
    listingId: UUID
    companyId: UUID
    message: str
    contactEmail: EmailStr
    contactPhone: str | None = None


class InquiryUpdateRequest(BaseModel):
    listingId: UUID | None = None
    companyId: UUID | None = None
    message: str | None = None
    contactEmail: EmailStr | None = None
    contactPhone: str | None = None
    status: InquiryStatus | None = None


class InquiryStatusUpdateRequest(BaseModel):
    status: InquiryStatus


class InquiryData(BaseModel):
    id: UUID
    listingId: UUID
    companyId: UUID
    message: str
    contactEmail: EmailStr
    contactPhone: str | None
    status: InquiryStatus
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
