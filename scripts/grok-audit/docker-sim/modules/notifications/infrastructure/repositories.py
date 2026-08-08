"""notifications repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import NotificationsEntity
from ..domain.repositories import NotificationsRepository
from .models import NotificationsModel


class NotificationsRepositoryImpl(NotificationsRepository):
    """Notifications repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[NotificationsEntity]:
        result = await self.session.execute(
            select(NotificationsModel).where(NotificationsModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return NotificationsEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[NotificationsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(NotificationsModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [NotificationsEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: NotificationsEntity) -> NotificationsEntity:
        model = NotificationsModel()
        self.session.add(model)
        await self.session.flush()
        return NotificationsEntity(id=str(model.id))
    
    async def update(self, entity: NotificationsEntity) -> NotificationsEntity:
        result = await self.session.execute(
            select(NotificationsModel).where(NotificationsModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return NotificationsEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(NotificationsModel).where(NotificationsModel.id == id)
        )
        await self.session.flush()
