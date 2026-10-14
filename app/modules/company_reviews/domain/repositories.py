"""company_reviews repository port (abstract)."""

from abc import ABC, abstractmethod


class CompanyReviewRepository(ABC):
    @abstractmethod
    async def get_by_id(self, review_id): ...

    @abstractmethod
    async def get_by_company_author(self, company_id, author_user_id): ...

    @abstractmethod
    async def list_by_company(
        self, company_id, *, statuses=None, page: int = 1, page_size: int = 20
    ) -> list: ...

    @abstractmethod
    async def count_by_company(self, company_id, *, statuses=None) -> int: ...

    @abstractmethod
    async def aggregate(self, company_id) -> dict: ...

    @abstractmethod
    async def create(self, review): ...

    @abstractmethod
    async def update(self, review): ...
