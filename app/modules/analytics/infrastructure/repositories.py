"""analytics repository implementations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import AnalyticsEntity
from ..domain.repositories import AnalyticsRepository
from .models import AnalyticsModel


class AnalyticsRepositoryImpl(AnalyticsRepository):
    """Analytics repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_entity(model: AnalyticsModel) -> AnalyticsEntity:
        return AnalyticsEntity(
            id=str(model.id),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, id: str) -> Optional[AnalyticsEntity]:
        result = await self.session.execute(
            select(AnalyticsModel).where(AnalyticsModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(AnalyticsModel).offset(offset).limit(limit)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        raise NotImplementedError("Analytics creation is not implemented")

    async def update(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        raise NotImplementedError("Analytics update is not implemented")

    async def delete(self, id: str) -> None:
        raise NotImplementedError("Analytics deletion is not implemented")
