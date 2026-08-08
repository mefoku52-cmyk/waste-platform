"""inquiries repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import InquiriesEntity
from ..domain.repositories import InquiriesRepository
from .models import InquiriesModel


class InquiriesRepositoryImpl(InquiriesRepository):
    """Inquiries repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[InquiriesEntity]:
        result = await self.session.execute(
            select(InquiriesModel).where(InquiriesModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return InquiriesEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[InquiriesEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(InquiriesModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [InquiriesEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: InquiriesEntity) -> InquiriesEntity:
        model = InquiriesModel()
        self.session.add(model)
        await self.session.flush()
        return InquiriesEntity(id=str(model.id))
    
    async def update(self, entity: InquiriesEntity) -> InquiriesEntity:
        result = await self.session.execute(
            select(InquiriesModel).where(InquiriesModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return InquiriesEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(InquiriesModel).where(InquiriesModel.id == id)
        )
        await self.session.flush()
