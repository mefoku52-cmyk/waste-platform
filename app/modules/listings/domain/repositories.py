from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.infrastructure.models import ListingsModel


class ListingsRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = ListingsModel

    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20, company_ids=None): ...

    @abstractmethod
    async def count_all(self, company_ids=None) -> int: ...

    @abstractmethod
    async def list_marketplace(self, page: int = 1, limit: int = 20, exclude_company_ids=None): ...

    @abstractmethod
    async def count_marketplace(self, exclude_company_ids=None) -> int: ...

    @abstractmethod
    async def get_company_status(self, company_id): ...

    @abstractmethod
    async def create(self, entity): ...

    @abstractmethod
    async def update(self, entity): ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...

    @abstractmethod
    async def find_matches(self, *, material_type: str, exclude_company_ids, limit: int = 20): ...
