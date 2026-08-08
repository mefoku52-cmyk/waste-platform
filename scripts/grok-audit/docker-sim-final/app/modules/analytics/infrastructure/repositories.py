"""analytics repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import AnalyticsEntity
from ..domain.repositories import AnalyticsRepository
from .models import AnalyticsModel


class AnalyticsRepositoryImpl(AnalyticsRepository):
    """Analytics repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[AnalyticsEntity]:
        result = await self.session.execute(
            select(AnalyticsModel).where(AnalyticsModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return AnalyticsEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(AnalyticsModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [AnalyticsEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        model = AnalyticsModel()
        self.session.add(model)
        await self.session.flush()
        return AnalyticsEntity(id=str(model.id))
    
    async def update(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        result = await self.session.execute(
            select(AnalyticsModel).where(AnalyticsModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return AnalyticsEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(AnalyticsModel).where(AnalyticsModel.id == id)
        )
        await self.session.flush()
