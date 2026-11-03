"""Async repository for listing photos."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.infrastructure.models.listing_photo import ListingPhotoModel


class ListingPhotoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, model: ListingPhotoModel) -> None:
        self._session.add(model)
        await self._session.flush()

    async def list_for_listing(self, listing_id: UUID, company_id: UUID) -> list[ListingPhotoModel]:
        stmt = select(ListingPhotoModel).where(
            ListingPhotoModel.listing_id == listing_id,
            ListingPhotoModel.company_id == company_id,
        ).order_by(ListingPhotoModel.sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())