"""documents domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import DocumentsEntity


class DocumentsRepository(ABC):
    """Documents repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[DocumentsEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[DocumentsEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: DocumentsEntity) -> DocumentsEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: DocumentsEntity) -> DocumentsEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
