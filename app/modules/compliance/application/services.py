"""compliance application services."""

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import ComplianceRecordEntity
from ..domain.repositories import ComplianceRecordRepository


class ComplianceRecordService:
    """ComplianceRecord service."""

    def __init__(self, repository: ComplianceRecordRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> ComplianceRecordEntity | None:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> list[ComplianceRecordEntity]:
        return await self.repository.list_all(page, limit)

    async def list_by_company_ids(self, company_ids, page: int = 1, limit: int = 20):
        return await self.repository.list_by_company_ids(company_ids, page, limit)

    async def count_by_company_ids(self, company_ids) -> int:
        return await self.repository.count_by_company_ids(company_ids)

    async def count_all(self) -> int:
        return await self.repository.count_all()

    async def create(self, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def update(self, id: str, entity: ComplianceRecordEntity) -> ComplianceRecordEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"ComplianceRecord {id} not found")
        entity.id = existing.id
        entity.created_at = existing.created_at
        entity.created_by_user_id = existing.created_by_user_id
        entity.validate()
        return await self.repository.update(entity)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"ComplianceRecord {id} not found")
        await self.repository.delete(id)
