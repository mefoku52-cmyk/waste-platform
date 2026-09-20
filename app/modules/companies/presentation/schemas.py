from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from app.modules.companies.domain.enums import CompanyStatus, CompanyType


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
    email: str | None = None
    phone: str | None = None
    websiteUrl: HttpUrl | None = None
    addressLine2: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    acceptedMaterialTypes: str | None = None


class CompanyUpdateRequest(BaseModel):
    legalName: str | None = None
    tradingName: str | None = None
    taxIdentifier: str | None = None
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
    companyType: CompanyType
    email: str | None
    phone: str | None
    websiteUrl: str | None
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


class CompanyResponse(BaseModel):
    data: CompanyData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedCompaniesResponse(BaseModel):
    items: list[CompanyData]
    meta: PaginationMeta


class CompanyStatusTransitionRequest(BaseModel):
    toStatus: CompanyStatus
