"""inquiries domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import InquiriesEntity


class InquiriesRepository(ABC):
    """Inquiries repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[InquiriesEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[InquiriesEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: InquiriesEntity) -> InquiriesEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: InquiriesEntity) -> InquiriesEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
