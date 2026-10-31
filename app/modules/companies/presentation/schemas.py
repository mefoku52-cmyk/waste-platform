from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from app.modules.companies.domain.enums import (
    CompanyStatus,
    CompanyType,
    SubscriptionTier,
)


class CompanyCreateRequest(BaseModel):
    legalName: str
    registrationNumber: str
    companyType: CompanyType
    countryCode: str
    addressLine1: str
    city: str
    postalCode: str
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool
    acceptedMaterialTypes: str | None = None
    tradingName: str | None = None
    taxIdentifier: str | None = None
    vatIdentifier: str | None = None
    email: str | None = None
    phone: str | None = None
    websiteUrl: HttpUrl | None = None
    logoUrl: str | None = None
    addressLine2: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CompanyUpdateRequest(BaseModel):
    legalName: str | None = None
    tradingName: str | None = None
    taxIdentifier: str | None = None
    vatIdentifier: str | None = None
    email: str | None = None
    phone: str | None = None
    websiteUrl: HttpUrl | None = None
    addressLine1: str | None = None
    addressLine2: str | None = None
    city: str | None = None
    postalCode: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CompanyData(BaseModel):
    id: UUID
    status: CompanyStatus
    legalName: str
    tradingName: str | None
    registrationNumber: str
    taxIdentifier: str | None
    vatIdentifier: str | None = None
    subscriptionTier: SubscriptionTier
    companyType: CompanyType
    email: str | None
    phone: str | None
    websiteUrl: str | None
    logoUrl: str | None = None
    countryCode: str
    addressLine1: str
    addressLine2: str | None
    city: str
    postalCode: str
    latitude: float | None
    longitude: float | None
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool
    acceptedMaterialTypes: str | None = None
    verificationSubmittedAt: datetime | None
    verificationReviewedAt: datetime | None
    verificationReviewedByUserId: UUID | None
    verifiedAt: datetime | None
    verifiedByUserId: UUID | None
    rejectedAt: datetime | None
    rejectedByUserId: UUID | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class CompanyDirectoryData(BaseModel):
    """Intentionally limited fields exposed by the cross-tenant directory."""

    id: UUID
    status: CompanyStatus
    legalName: str
    tradingName: str | None
    registrationNumber: str
    companyType: CompanyType
    logoUrl: str | None = None
    countryCode: str
    city: str
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool


class CompanyResponse(BaseModel):
    data: CompanyData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedCompaniesResponse(BaseModel):
    # Directory entries use a strictly smaller public schema; ordinary list
    # results retain the existing full member/admin response schema.
    items: list[CompanyData | CompanyDirectoryData]
    meta: PaginationMeta


class CompanyStatusTransitionRequest(BaseModel):
    toStatus: CompanyStatus


class SubscriptionTierUpdateRequest(BaseModel):
    tier: SubscriptionTier
