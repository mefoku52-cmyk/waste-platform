"""listings application services."""

from typing import List, Optional

from ..domain.entities import ListingsEntity
from ..domain.repositories import ListingsRepository


class ListingsService:
    """Listings service."""
    
    def __init__(self, repository: ListingsRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ListingsEntity]:
        return await self.repository.list_all(page, limit)
