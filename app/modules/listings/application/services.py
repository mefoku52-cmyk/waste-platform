"""listings application services."""

from typing import List, Optional

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository


class ListingsService:
    """Listings service."""

    def __init__(self, repository: ListingsRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20, company_ids=None) -> List[ListingsEntity]:
        return await self.repository.list_all(page, limit, company_ids=company_ids)

    async def count_all(self, company_ids=None) -> int:
        return await self.repository.count_all(company_ids=company_ids)

    async def list_marketplace(self, page: int = 1, limit: int = 20, exclude_company_ids=None):
        return await self.repository.list_marketplace(page, limit, exclude_company_ids=exclude_company_ids)

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
        from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError
        from app.modules.listings.domain.enums import ListingsStatus
        from datetime import datetime

        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")

        # overenie firmy cez raw SQL v repo
        status_val = await self.repository.get_company_status(existing.company_id)
        if status_val != "verified":
            raise ValidationDomainError(
                "Publikovať môže len overená firma (status verified). Najprv over firmu."
            )

        existing.status = ListingsStatus.PUBLISHED
        existing.updated_at = datetime.utcnow()
        return await self.repository.update(existing)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Listing {id} not found")
        await self.repository.delete(id)
