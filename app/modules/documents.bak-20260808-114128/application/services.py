"""documents application services."""

from typing import List, Optional

from ..domain.entities import DocumentsEntity
from ..domain.repositories import DocumentsRepository


class DocumentsService:
    """Documents service."""
    
    def __init__(self, repository: DocumentsRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[DocumentsEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[DocumentsEntity]:
        return await self.repository.list_all(page, limit)
