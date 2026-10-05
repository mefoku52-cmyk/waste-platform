from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.infrastructure.models import DocumentModel


class DocumentRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = DocumentModel

    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def get_by_file_url(self, file_url: str): ...

    @abstractmethod
    async def list_by_company_ids(self, company_ids, page: int = 1, limit: int = 20): ...

    @abstractmethod
    async def count_by_company_ids(self, company_ids) -> int: ...

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20): ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def create(self, entity): ...

    @abstractmethod
    async def update(self, entity): ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...
