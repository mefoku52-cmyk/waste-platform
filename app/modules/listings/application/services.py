"""listings application services."""

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository


class ListingsService:
    """Listings service."""

    def __init__(self, repository: ListingsRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> ListingsEntity | None:
        return await self.repository.get_by_id(id)

    async def list_all(
        self, page: int = 1, limit: int = 20, company_ids=None
    ) -> list[ListingsEntity]:
        return await self.repository.list_all(page, limit, company_ids=company_ids)

    async def count_all(self, company_ids=None) -> int:
        return await self.repository.count_all(company_ids=company_ids)

    async def list_marketplace(self, page: int = 1, limit: int = 20, exclude_company_ids=None):
        return await self.repository.list_marketplace(
            page, limit, exclude_company_ids=exclude_company_ids
        )

    async def count_marketplace(self, exclude_company_ids=None) -> int:
        return await self.repository.count_marketplace(exclude_company_ids=exclude_company_ids)

    async def create(self, entity: ListingsEntity) -> ListingsEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def update(self, id: str, entity: ListingsEntity) -> ListingsEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")
        entity.id = existing.id
        entity.created_at = existing.created_at
        entity.created_by_user_id = existing.created_by_user_id
        entity.validate()
        return await self.repository.update(entity)

    async def publish(self, id: str):
        """draft → published, len ak firma listing-u je verified."""
        from datetime import datetime

        from app.modules.listings.domain.enums import ListingsStatus
        from app.shared.domain.exceptions import (
            NotFoundDomainError,
            ValidationDomainError,
        )

        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")

        # overenie firmy cez raw SQL v repo
        status_val = await self.repository.get_company_status(existing.company_id)
        if status_val != "verified":
            raise ValidationDomainError(
                "Publikovať môže len overená firma (status verified). Najprv over firmu."
            )
        if not (getattr(existing, "location", None) or "").strip():
            raise ValidationDomainError("Publikovať môžeš len ponuku s lokalitou.")

        existing.status = ListingsStatus.PUBLISHED
        existing.updated_at = datetime.now()
        return await self.repository.update(existing)

    async def promote(self, id: str, *, days: int, tier: str) -> None:
        """Zvýrazní ponuku na určený počet dní."""
        from app.shared.domain.exceptions import ValidationDomainError

        if days not in (7, 30):
            raise ValidationDomainError("Počet dní musí byť 7 alebo 30.")
        if tier not in ("top", "gold"):
            raise ValidationDomainError("Tier musí byť 'top' alebo 'gold'.")

        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")
        await self.repository.promote(id, days=days, tier=tier)

    async def unpromote(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")
        await self.repository.unpromote(id)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")
        await self.repository.delete(id)

    async def find_matches(self, *, material_type: str, exclude_company_ids, limit: int = 20):
        return await self.repository.find_matches(
            material_type=material_type,
            exclude_company_ids=exclude_company_ids or [],
            limit=limit,
        )

    async def record_view(self, listing_id, user_id) -> None:
        """Zapise jedno zobrazenie ponuky konkretnym userom."""
        existing = await self.repository.get_by_id(listing_id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {listing_id} not found")
        await self.repository.record_view(listing_id, user_id)

    async def get_stats(self, listing_id: str, owner_company_ids=None) -> dict:
        """Vrati {views, unique_viewers}. Iba vlastnik (company v zozname) to smie vidiet."""
        existing = await self.repository.get_by_id(listing_id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {listing_id} not found")
        owner_ids = {str(x) for x in (owner_company_ids or []) if x is not None}
        if owner_ids and str(existing.company_id) not in owner_ids:
            from app.shared.domain.exceptions import ValidationDomainError

            raise ValidationDomainError("Statistiky moze vidiet len vlastnik ponuky.")
        stats = await self.repository.get_listing_stats(listing_id)
        return {"views": stats["views"], "uniqueViewers": stats["unique_viewers"]}
