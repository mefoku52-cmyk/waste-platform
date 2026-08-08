"""analytics application services."""

from typing import List, Optional

from ..domain.entities import AnalyticsEntity
from ..domain.repositories import AnalyticsRepository


class AnalyticsService:
    """Analytics service."""
    
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository
    
    async def get_by_id(self, id: str) -> Optional[AnalyticsEntity]:
        return await self.repository.get_by_id(id)
    
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEntity]:
        return await self.repository.list_all(page, limit)
