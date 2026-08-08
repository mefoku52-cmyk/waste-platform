"""analytics domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import AnalyticsEntity


class AnalyticsRepository(ABC):
    """Analytics repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[AnalyticsEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AnalyticsEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: AnalyticsEntity) -> AnalyticsEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
