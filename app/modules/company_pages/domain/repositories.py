"""company_pages repository ports (abstract)."""

from abc import ABC, abstractmethod


class CompanyPageRepository(ABC):
    @abstractmethod
    async def get_by_company_id(self, company_id): ...

    @abstractmethod
    async def get_by_id(self, page_id): ...

    @abstractmethod
    async def get_by_slug(self, slug: str): ...

    @abstractmethod
    async def list_slugs(self) -> list[str]: ...

    @abstractmethod
    async def list_published_slugs(self) -> list[tuple[str, object]]: ...

    @abstractmethod
    async def create(self, page): ...

    @abstractmethod
    async def update(self, page): ...


class CompanyPhotoRepository(ABC):
    @abstractmethod
    async def list_by_company(self, company_id) -> list: ...

    @abstractmethod
    async def get_by_id(self, photo_id): ...

    @abstractmethod
    async def count_by_company(self, company_id) -> int: ...

    @abstractmethod
    async def count_created_since(self, company_id, since) -> int: ...

    @abstractmethod
    async def count_uploaded_since(self, company_id, since) -> int: ...

    @abstractmethod
    async def create(self, photo): ...

    @abstractmethod
    async def update(self, photo): ...

    @abstractmethod
    async def delete(self, photo_id) -> None: ...
