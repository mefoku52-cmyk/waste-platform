"""admin domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import AdminEntity


class AdminRepository(ABC):
    """Admin repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[AdminEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[AdminEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: AdminEntity) -> AdminEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: AdminEntity) -> AdminEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
