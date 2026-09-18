"""inquiries application services."""

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import InquiryEntity
from ..domain.repositories import InquiryRepository


class InquiryService:
    """Inquiry service."""

    def __init__(self, repository: InquiryRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> InquiryEntity | None:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> list[InquiryEntity]:
        return await self.repository.list_all(page, limit)

    async def count_all(self) -> int:
        return await self.repository.count_all()

    async def list_sent(self, page: int = 1, limit: int = 20, company_ids=None):
        return await self.repository.list_sent(page, limit, company_ids=company_ids)

    async def count_sent(self, company_ids=None) -> int:
        return await self.repository.count_sent(company_ids=company_ids)

    async def list_received(self, page: int = 1, limit: int = 20, seller_company_ids=None):
        return await self.repository.list_received(
            page, limit, seller_company_ids=seller_company_ids
        )

    async def count_received(self, seller_company_ids=None) -> int:
        return await self.repository.count_received(seller_company_ids=seller_company_ids)

    async def seller_owns_inquiry(self, id: str, seller_company_ids=None) -> bool:
        """True ak listing danej inquiry patri niektorej z `seller_company_ids`."""
        return await self.repository.seller_owns_inquiry(id, seller_company_ids or [])

    async def create(self, entity: InquiryEntity) -> InquiryEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def update(self, id: str, entity: InquiryEntity) -> InquiryEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Inquiry {id} not found")
        entity.id = existing.id
        entity.created_at = existing.created_at
        entity.created_by_user_id = existing.created_by_user_id
        entity.validate()
        return await self.repository.update(entity)

    async def update_status_as_seller(self, id: str, new_status, seller_company_ids=None):
        """Zmení status len ak listing patrí seller_company_ids."""
        from app.shared.domain.exceptions import (
            NotFoundDomainError,
            ValidationDomainError,
        )

        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Inquiry {id} not found")
        ok = await self.repository.seller_owns_inquiry(id, seller_company_ids or [])
        if not ok:
            raise ValidationDomainError("Nie si predávajúci tejto ponuky")
        existing.status = new_status
        from datetime import datetime

        existing.updated_at = datetime.now()
        return await self.repository.update(existing)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"Inquiry {id} not found")
        await self.repository.delete(id)
