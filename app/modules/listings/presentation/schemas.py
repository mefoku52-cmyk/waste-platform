"""listings API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    status: str | None = None
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
    status: str
    companyId: UUID | None
    description: str | None
    imageUrl: str | None = None
    createdAt: datetime
    updatedAt: datetime


class ListingResponse(BaseModel):
    data: ListingData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedListingsResponse(BaseModel):
    items: list[ListingData]
    meta: PaginationMeta
