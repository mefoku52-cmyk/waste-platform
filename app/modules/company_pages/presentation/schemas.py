"""company_pages API schemas (private + public)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ─────────────────────────────────────────────────────────────
# PRIVATE (tenant) — editor
# ─────────────────────────────────────────────────────────────


class CompanyPageUpsertRequest(BaseModel):
    slug: str | None = None
    displayName: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=255)
    aboutShort: str | None = Field(default=None, max_length=600)
    aboutLong: str | None = None
    services: str | None = None
    specialization: str | None = None
    certifications: str | None = None
    openingHours: str | None = Field(default=None, max_length=500)
    languages: str | None = Field(default=None, max_length=255)
    categories: str | None = Field(default=None, max_length=500)
    area: str | None = Field(default=None, max_length=255)
    publicEmail: EmailStr | None = None
    publicPhone: str | None = Field(default=None, max_length=64)
    publicWebsite: str | None = Field(default=None, max_length=512)
    seoTitle: str | None = Field(default=None, max_length=255)
    seoDescription: str | None = Field(default=None, max_length=320)


class CompanyPagePhotoCreateRequest(BaseModel):
    fileUrl: str = Field(..., max_length=1024)
    caption: str | None = Field(default=None, max_length=500)
    altText: str | None = Field(default=None, max_length=500)


class CompanyPagePhotoUpdateRequest(BaseModel):
    caption: str | None = Field(default=None, max_length=500)
    altText: str | None = Field(default=None, max_length=500)


class CompanyPageReorderRequest(BaseModel):
    orderedIds: list[str]


class CompanyPageData(BaseModel):
    id: str | None = None
    companyId: str
    slug: str
    status: str
    exists: bool
    displayName: str | None
    tagline: str | None
    aboutShort: str | None
    aboutLong: str | None
    services: str | None
    specialization: str | None
    certifications: str | None
    openingHours: str | None
    languages: str | None
    categories: str | None
    area: str | None
    publicEmail: str | None
    publicPhone: str | None
    publicWebsite: str | None
    seoTitle: str | None
    seoDescription: str | None
    publishedAt: datetime | None
    createdAt: datetime | None
    updatedAt: datetime | None
    missingForPublish: list[str] = []


class CompanyPageResponse(BaseModel):
    data: CompanyPageData


class CompanyPhotoData(BaseModel):
    id: str
    fileUrl: str
    caption: str | None
    altText: str | None
    position: int
    isPrimary: bool
    createdAt: datetime | None = None


class CompanyPagePhotosResponse(BaseModel):
    items: list[CompanyPhotoData]
    meta: dict


class SlugAvailableResponse(BaseModel):
    slug: str
    available: bool
    reason: str


# ─────────────────────────────────────────────────────────────
# PUBLIC — verejná firemná stránka
# ─────────────────────────────────────────────────────────────


class PublicCompanyPhoto(BaseModel):
    url: str
    caption: str | None
    altText: str | None
    position: int
    isPrimary: bool


class PublicCompanyListing(BaseModel):
    id: str
    title: str
    materialType: str | None
    quantity: float | None
    unit: str | None
    price: float | None
    currency: str | None
    location: str | None
    condition: str | None
    imageUrl: str | None = None


class PublicCompanyReview(BaseModel):
    id: str
    rating: int
    title: str | None
    body: str | None
    createdAt: datetime | None = None


class PublicCompanyInfo(BaseModel):
    displayName: str
    legalName: str | None
    companyType: str | None
    city: str | None
    countryCode: str | None
    verified: bool
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool
    logoUrl: str | None = None


class PublicSitemapEntry(BaseModel):
    slug: str
    updatedAt: datetime | None = None


class PublicSitemapResponse(BaseModel):
    items: list[PublicSitemapEntry]
    meta: dict


class PublicCompanyPageResponse(BaseModel):
    slug: str
    publishedAt: datetime | None
    displayName: str
    tagline: str | None
    aboutShort: str | None
    aboutLong: str | None
    services: str | None
    specialization: str | None
    certifications: str | None
    openingHours: str | None
    languages: str | None
    categories: str | None
    area: str | None
    publicEmail: str | None
    publicPhone: str | None
    publicWebsite: str | None
    seoTitle: str | None = None
    seoDescription: str | None = None
    company: PublicCompanyInfo
    photos: list[PublicCompanyPhoto]
    listings: list[PublicCompanyListing]
    ratingAverage: float | None = None
    ratingCount: int = 0
    reviews: list[PublicCompanyReview] = []
