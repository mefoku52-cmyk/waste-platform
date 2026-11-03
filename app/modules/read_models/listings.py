"""CQRS light read model for marketplace listings."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ListingReadModel(BaseModel):
    id: UUID
    title: str
    material_type: str | None
    quantity: float | None
    unit: str | None
    price: float | None
    currency: str | None
    status: str
    company_id: UUID
    promoted_until: datetime | None = None
    updated_at: datetime


class MarketplaceProjection:
    """In-memory projection; replace with Redis or materialized view in production."""

    def __init__(self) -> None:
        self._items: dict[UUID, ListingReadModel] = {}

    def upsert(self, item: ListingReadModel) -> None:
        self._items[item.id] = item

    def remove(self, listing_id: UUID) -> None:
        self._items.pop(listing_id, None)

    def search(self, material_type: str | None = None, limit: int = 50) -> list[ListingReadModel]:
        results = list(self._items.values())
        if material_type:
            results = [r for r in results if r.material_type == material_type]
        return results[:limit]