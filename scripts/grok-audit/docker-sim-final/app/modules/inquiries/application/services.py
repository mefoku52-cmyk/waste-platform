"""inquiries application services."""

from typing import List, Optional

from ..domain.entities import InquiriesEntity
from ..domain.repositories import InquiriesRepository


class InquiriesService:
    """Inquiries service."""
    
    def __init__(self, repository: InquiriesRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[InquiriesEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[InquiriesEntity]:
        return await self.repository.list_all(page, limit)
