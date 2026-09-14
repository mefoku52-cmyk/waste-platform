from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.listings.application.services import ListingsService
from app.modules.listings.domain.entities import ListingsEntity
from app.modules.listings.domain.enums import ListingsStatus
from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError


def _now():
    return datetime.now(UTC)


def _entity(**overrides) -> ListingsEntity:
    data = {
        "title": "PET flakes",
        "material_type": "PET",
        "quantity": 10.0,
        "unit": "kg",
        "condition": "clean",
        "location": "BA",
        "company_id": str(uuid4()),
        "status": ListingsStatus.DRAFT,
        "price": 1.5,
        "currency": "EUR",
        "description": "test",
        "image_url": None,
    }
    data.update(overrides)
    try:
        return ListingsEntity(**data)
    except TypeError:
        data.update(
            id=str(uuid4()),
            created_at=_now(),
            created_by_user_id=None,
            updated_at=_now(),
            updated_by_user_id=None,
        )
        return ListingsEntity(**{k: v for k, v in data.items() if True})


class FakeListingsRepo:
    def __init__(self):
        self.items = []

    async def get_by_id(self, id: str):
        for item in self.items:
            if str(getattr(item, "id", None)) == str(id):
                return item
        return None

    async def list_all(self, page=1, limit=20, company_ids=None):
        return list(self.items)

    async def count_all(self, company_ids=None) -> int:
        return len(self.items)

    async def list_marketplace(self, page=1, limit=20, exclude_company_ids=None):
        return list(self.items)

    async def count_marketplace(self, exclude_company_ids=None) -> int:
        return len(self.items)

    async def create(self, entity):
        if getattr(entity, "id", None) is None:
            entity.id = str(uuid4())
        self.items.append(entity)
        return entity

    async def update(self, entity):
        for i, item in enumerate(self.items):
            if str(item.id) == str(entity.id):
                self.items[i] = entity
                return entity
        self.items.append(entity)
        return entity

    async def publish(self, id: str):
        item = await self.get_by_id(id)
        return item

    async def delete(self, id: str) -> None:
        self.items = [i for i in self.items if str(i.id) != str(id)]

    async def find_matches(self, *, material_type, exclude_company_ids, limit=20):
        return [i for i in self.items if i.material_type == material_type][:limit]

    async def record_view(self, listing_id, user_id) -> None:
        return None

    async def get_stats(self, listing_id: str, owner_company_ids=None) -> dict:
        return {"views": 0}

    async def get_listing_stats(self, listing_id: str) -> dict:
        return {"views": 0, "unique_viewers": 0}

    async def get_company_status(self, company_id: str) -> str:
        return "verified"


@pytest.fixture
def service():
    return ListingsService(FakeListingsRepo())


@pytest.mark.asyncio
async def test_create_and_get(service):
    created = await service.create(_entity())
    got = await service.get_by_id(str(created.id))
    assert got is not None
    assert got.title == "PET flakes"


@pytest.mark.asyncio
async def test_create_rejects_empty_title(service):
    with pytest.raises(ValidationDomainError):
        await service.create(_entity(title=""))


@pytest.mark.asyncio
async def test_update_missing(service):
    with pytest.raises(NotFoundDomainError):
        await service.update("missing", _entity())


@pytest.mark.asyncio
async def test_list_and_count(service):
    await service.create(_entity())
    await service.create(_entity(title="HDPE"))
    items = await service.list_all()
    assert await service.count_all() == 2
    assert len(items) == 2
    assert await service.count_marketplace() == 2


@pytest.mark.asyncio
async def test_delete(service):
    created = await service.create(_entity())
    await service.delete(str(created.id))
    assert await service.get_by_id(str(created.id)) is None


@pytest.mark.asyncio
async def test_find_matches_and_stats(service):
    created = await service.create(_entity(material_type="PET"))
    matches = await service.find_matches(material_type="PET", exclude_company_ids=None)
    assert len(matches) >= 1
    stats = await service.get_stats(str(created.id))
    assert isinstance(stats, dict)
    await service.record_view(str(created.id), user_id="u1")


@pytest.mark.asyncio
async def test_publish_verified_company(service):
    created = await service.create(_entity())
    published = await service.publish(str(created.id))
    name = getattr(published.status, "name", str(published.status))
    value = getattr(published.status, "value", str(published.status))
    assert "PUBLISH" in str(name).upper() or "publish" in str(value).lower()


@pytest.mark.asyncio
async def test_publish_missing(service):
    with pytest.raises(NotFoundDomainError):
        await service.publish("nope")
