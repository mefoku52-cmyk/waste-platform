"""compliance domain repositories."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import ComplianceEntity


class ComplianceRepository(ABC):
    """Compliance repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ComplianceEntity]:
        pass
    
    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20) -> List[ComplianceEntity]:
        pass
    
    @abstractmethod
    async def create(self, entity: ComplianceEntity) -> ComplianceEntity:
        pass
    
    @abstractmethod
    async def update(self, entity: ComplianceEntity) -> ComplianceEntity:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
