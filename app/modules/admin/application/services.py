"""admin application services."""

from typing import List, Optional

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import AdminAuditEntryEntity
from ..domain.repositories import AdminAuditEntryRepository


class AdminAuditEntryService:
    """AdminAuditEntry service."""

    def __init__(self, repository: AdminAuditEntryRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> Optional[AdminAuditEntryEntity]:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminAuditEntryEntity]:
        return await self.repository.list_all(page, limit)

    async def list_by_actor(self, actor_user_id, page: int = 1, limit: int = 20):
        return await self.repository.list_by_actor(actor_user_id, page, limit)

    async def count_by_actor(self, actor_user_id) -> int:
        return await self.repository.count_by_actor(actor_user_id)

    async def count_all(self) -> int:
        return await self.repository.count_all()

    async def create(self, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def update(self, id: str, entity: AdminAuditEntryEntity) -> AdminAuditEntryEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"AdminAuditEntry {id} not found")
        entity.id = existing.id
        entity.created_at = existing.created_at
        entity.created_by_user_id = existing.created_by_user_id
        entity.validate()
        return await self.repository.update(entity)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"AdminAuditEntry {id} not found")
        await self.repository.delete(id)
