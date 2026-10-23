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
    actorEmail: str | None = None
    actorName: str | None = None
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


class PaginatedAdminAuditEntriesResponse(BaseModel):
    items: list[AdminAuditEntryData]
    meta: PaginationMeta


class AdminCompanyListItem(BaseModel):
    id: str
    status: str
    legalName: str
    tradingName: str | None = None
    registrationNumber: str
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    countryCode: str | None = None
    subscriptionTier: str | None = None
    companyType: str | None = None
    photoCount: int = 0
    createdAt: datetime | None = None


class AdminCompaniesResponse(BaseModel):
    items: list[AdminCompanyListItem]
    meta: PaginationMeta


class AdminCompanyMembershipData(BaseModel):
    userId: str
    email: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    role: str
    status: str
    isPrimaryContact: bool = False


class AdminCompanyPhotoData(BaseModel):
    id: str
    fileUrl: str
    caption: str | None = None
    altText: str | None = None
    position: int = 0
    isPrimary: bool = False
    createdAt: datetime | None = None


class AdminCompanyDetailData(AdminCompanyListItem):
    taxIdentifier: str | None = None
    vatIdentifier: str | None = None
    websiteUrl: str | None = None
    addressLine1: str | None = None
    addressLine2: str | None = None
    postalCode: str | None = None
    sellerCapability: bool = False
    buyerCapability: bool = False
    logisticsCapability: bool = False
    verificationSubmittedAt: datetime | None = None
    verifiedAt: datetime | None = None
    rejectedAt: datetime | None = None
    pageSlug: str | None = None
    pageStatus: str | None = None
    publicEmail: str | None = None
    publicPhone: str | None = None
    counts: dict = {}
    memberships: list[AdminCompanyMembershipData] = []
    photos: list[AdminCompanyPhotoData] = []


class AdminCompanyDetailResponse(BaseModel):
    data: AdminCompanyDetailData
