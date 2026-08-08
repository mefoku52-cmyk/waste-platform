"""analytics application services."""

from typing import List, Optional

from app.shared.domain.exceptions import NotFoundDomainError

from ..domain.entities import AnalyticsEventEntity
from ..domain.repositories import AnalyticsEventRepository


class AnalyticsEventService:
    """AnalyticsEvent service."""

    def __init__(self, repository: AnalyticsEventRepository):
        self.repository = repository

    async def get_by_id(self, id: str) -> Optional[AnalyticsEventEntity]:
        return await self.repository.get_by_id(id)

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEventEntity]:
        return await self.repository.list_all(page, limit)

    async def count_all(self) -> int:
        return await self.repository.count_all()

    async def create(self, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        entity.validate()
        return await self.repository.create(entity)

    async def update(self, id: str, entity: AnalyticsEventEntity) -> AnalyticsEventEntity:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"AnalyticsEvent {id} not found")
        entity.id = existing.id
        entity.created_at = existing.created_at
        entity.created_by_user_id = existing.created_by_user_id
        entity.validate()
        return await self.repository.update(entity)

    async def delete(self, id: str) -> None:
        existing = await self.repository.get_by_id(id)
        if existing is None:
            raise NotFoundDomainError(f"AnalyticsEvent {id} not found")
        await self.repository.delete(id)
