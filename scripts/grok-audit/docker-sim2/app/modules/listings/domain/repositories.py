"""listings domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import ListingsEntity


class ListingsRepository(ABC):
    """Listings repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ListingsEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ListingsEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: ListingsEntity) -> ListingsEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: ListingsEntity) -> ListingsEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
