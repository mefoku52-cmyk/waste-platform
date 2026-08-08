"""listings repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository
from .models import ListingsModel


class ListingsRepositoryImpl(ListingsRepository):
    """Listings repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        result = await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return ListingsEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ListingsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(ListingsModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [ListingsEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: ListingsEntity) -> ListingsEntity:
        model = ListingsModel()
        self.session.add(model)
        await self.session.flush()
        return ListingsEntity(id=str(model.id))
    
    async def update(self, entity: ListingsEntity) -> ListingsEntity:
        result = await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return ListingsEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == id)
        )
        await self.session.flush()
