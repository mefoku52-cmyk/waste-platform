"""documents repository implementations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities import DocumentsEntity
from ..domain.repositories import DocumentsRepository
from .models import DocumentsModel


class DocumentsRepositoryImpl(DocumentsRepository):
    """Documents repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[DocumentsEntity]:
        result = await self.session.execute(
            select(DocumentsModel).where(DocumentsModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            return DocumentsEntity(id=str(model.id))
        return None
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[DocumentsEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(DocumentsModel).offset(offset).limit(limit)
        )
        models = result.scalars().all()
        return [DocumentsEntity(id=str(m.id)) for m in models]
    
    async def create(self, entity: DocumentsEntity) -> DocumentsEntity:
        model = DocumentsModel()
        self.session.add(model)
        await self.session.flush()
        return DocumentsEntity(id=str(model.id))
    
    async def update(self, entity: DocumentsEntity) -> DocumentsEntity:
        result = await self.session.execute(
            select(DocumentsModel).where(DocumentsModel.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.flush()
            return DocumentsEntity(id=str(model.id))
        raise ValueError("Entity not found")
    
    async def delete(self, id: str) -> None:
        await self.session.execute(
            select(DocumentsModel).where(DocumentsModel.id == id)
        )
        await self.session.flush()
