from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inquiries.infrastructure.models import InquiryModel


class InquiryRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = InquiryModel

    @abstractmethod
    async def get_by_id(self, id: str): ...

    @abstractmethod
    async def list_all(self, page: int = 1, limit: int = 20): ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def list_sent(self, page: int = 1, limit: int = 20, company_ids=None): ...

    @abstractmethod
    async def count_sent(self, company_ids=None) -> int: ...

    @abstractmethod
    async def list_received(self, page: int = 1, limit: int = 20, seller_company_ids=None): ...

    @abstractmethod
    async def count_received(self, seller_company_ids=None) -> int: ...

    @abstractmethod
    async def seller_owns_inquiry(self, inquiry_id: str, seller_company_ids=None) -> bool: ...

    @abstractmethod
    async def create(self, entity): ...

    @abstractmethod
    async def update(self, entity): ...

    @abstractmethod
    async def delete(self, id: str) -> None: ...
