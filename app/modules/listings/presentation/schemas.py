"""listings API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.listings.domain.enums import ListingsStatus


class ListingCreateRequest(BaseModel):
    title: str
    materialType: str
    quantity: float = Field(gt=0)
    unit: str
    price: float | None = None
    currency: str = "EUR"
    condition: str
    location: str
    companyId: UUID
    description: str | None = None
    imageUrl: str | None = None


class ListingUpdateRequest(BaseModel):
    title: str | None = None
    materialType: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    price: float | None = None
    currency: str | None = None
    condition: str | None = None
    location: str | None = None
    status: ListingsStatus | None = None
    description: str | None = None
    imageUrl: str | None = None


class ListingData(BaseModel):
    id: UUID
    title: str
    materialType: str
    quantity: float
    unit: str
    price: float | None
    currency: str
    condition: str
    location: str
    status: ListingsStatus
    companyId: UUID | None
    description: str | None
    imageUrl: str | None = None
    createdAt: datetime
    updatedAt: datetime
    promotedUntil: datetime | None = None
    promotedTier: str | None = None


class ListingResponse(BaseModel):
    data: ListingData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedListingsResponse(BaseModel):
    items: list[ListingData]
    meta: PaginationMeta


class ListingStatsResponse(BaseModel):
    views: int
    uniqueViewers: int


class PromoteListingRequest(BaseModel):
    days: int = Field(default=7, ge=7, le=30)
    tier: str = Field(default="top", pattern="^(top|gold)$")
    stripe_session_id: str | None = Field(
        default=None, description="Overeny Stripe Checkout Session ID"
    )


class PromoteListingResponse(BaseModel):
    ok: bool
    promotedUntil: datetime | None = None
    promotedTier: str | None = None


class AiDraftRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    companyId: UUID | None = None
    persona: str = Field(default="bystry", max_length=20)


class AiDraftData(BaseModel):
    title: str
    description: str
    materialType: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    condition: str | None = None
    currency: str | None = None
    price: float | None = None


class AiDraftResponse(BaseModel):
    data: AiDraftData
    provider: str  # "groq" alebo "fallback"
