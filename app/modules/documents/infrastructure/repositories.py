"""documents repository implementations."""

from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import DocumentEntity
from ..domain.repositories import DocumentRepository
from .mappers import to_domain, to_model
from .models import DocumentModel


class DocumentRepositoryImpl(DocumentRepository):
    """Document repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str) -> Optional[DocumentEntity]:
        result = await self.session.execute(select(DocumentModel).where(DocumentModel.id == id))
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_all(self, page: int = 1, limit: int = 20) -> List[DocumentEntity]:
        offset = (page - 1) * limit
        result = await self.session.execute(select(DocumentModel).order_by(DocumentModel.created_at.desc()).offset(offset).limit(limit))
        models = result.scalars().all()
        return [to_domain(m) for m in models]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(DocumentModel))
        return int(result.scalar_one())

    async def create(self, entity: DocumentEntity) -> DocumentEntity:
        model = to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return to_domain(model)

    async def update(self, entity: DocumentEntity) -> DocumentEntity:
        model = await self.session.get(DocumentModel, entity.id)
        if model is None:
            raise ValueError("Entity not found")
        model.title = entity.title
        model.document_type = entity.document_type
        model.file_url = entity.file_url
        model.company_id = entity.company_id
        model.listing_id = entity.listing_id
        model.status = entity.status.value
        model.updated_at = entity.updated_at
        model.updated_by_user_id = entity.updated_by_user_id
        await self.session.flush()
        await self.session.refresh(model)
        return to_domain(model)

    async def delete(self, id: str) -> None:
        await self.session.execute(sql_delete(DocumentModel).where(DocumentModel.id == id))
        await self.session.flush()
