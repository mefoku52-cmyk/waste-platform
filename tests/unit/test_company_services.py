from uuid import uuid4

import pytest

from app.modules.companies.application.services import (
    CreateCompanyService,
    GetCompanyService,
    ListCompaniesService,
    UpdateCompanyService,
)
from app.modules.companies.domain.enums import CompanyType
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


def _company_type() -> str:
    first = next(iter(CompanyType))
    return first.value if hasattr(first, "value") else str(first)


class FakeCompanyRepo:
    def __init__(self):
        self.items = []

    async def add(self, company) -> None:
        self.items.append(company)

    async def get_by_id(self, company_id):
        for item in self.items:
            if item.id == company_id:
                return item
        return None

    async def list(self, **kwargs):
        return list(self.items), len(self.items)

    async def update(self, company) -> None:
        for i, item in enumerate(self.items):
            if item.id == company.id:
                self.items[i] = company
                return
        self.items.append(company)


class FakeMembershipRepo:
    def __init__(self):
        self.items = []

    async def add(self, membership) -> None:
        self.items.append(membership)


def _create_kwargs(**overrides):
    data = {
        "legal_name": "Waste s.r.o.",
        "trading_name": "Waste",
        "registration_number": "12345678",
        "tax_identifier": "SK12345678",
        "company_type": _company_type(),
        "email": "ops@example.com",
        "phone": "+421900000000",
        "website_url": "https://example.com",
        "country_code": "sk",
        "address_line_1": "Hlavna 1",
        "address_line_2": None,
        "city": "Bratislava",
        "postal_code": "81101",
        "latitude": 48.14,
        "longitude": 17.10,
        "seller_capability": True,
        "buyer_capability": False,
        "logistics_capability": False,
        "actor_user_id": uuid4(),
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_create_company_persists_and_makes_owner():
    companies = FakeCompanyRepo()
    memberships = FakeMembershipRepo()
    svc = CreateCompanyService(
        repo=companies,
        membership_repo=memberships,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )
    dto = await svc.execute(**_create_kwargs())
    assert dto.legal_name == "Waste s.r.o."
    assert len(companies.items) == 1
    assert len(memberships.items) == 1
    assert companies.items[0].country_code == "SK"


@pytest.mark.asyncio
async def test_create_company_without_actor_skips_membership():
    companies = FakeCompanyRepo()
    memberships = FakeMembershipRepo()
    svc = CreateCompanyService(
        repo=companies,
        membership_repo=memberships,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )
    await svc.execute(**_create_kwargs(actor_user_id=None))
    assert len(companies.items) == 1
    assert memberships.items == []


@pytest.mark.asyncio
async def test_get_company_found():
    companies = FakeCompanyRepo()
    memberships = FakeMembershipRepo()
    created = await CreateCompanyService(
        repo=companies,
        membership_repo=memberships,
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    ).execute(**_create_kwargs(actor_user_id=None))
    dto = await GetCompanyService(companies).execute(created.id)
    assert dto.id == created.id


@pytest.mark.asyncio
async def test_get_company_missing():
    with pytest.raises(NotFoundDomainError):
        await GetCompanyService(FakeCompanyRepo()).execute(uuid4())


@pytest.mark.asyncio
async def test_list_companies_returns_total():
    companies = FakeCompanyRepo()
    svc = CreateCompanyService(
        repo=companies,
        membership_repo=FakeMembershipRepo(),
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )
    await svc.execute(**_create_kwargs(actor_user_id=None, legal_name="A"))
    await svc.execute(**_create_kwargs(actor_user_id=None, legal_name="B"))
    items, total = await ListCompaniesService(companies).execute(
        status=None,
        company_type=None,
        seller_capability=None,
        buyer_capability=None,
        logistics_capability=None,
        q=None,
        page=1,
        page_size=20,
    )
    assert total == 2
    assert len(items) == 2


@pytest.mark.asyncio
async def test_update_company_changes_name():
    companies = FakeCompanyRepo()
    created = await CreateCompanyService(
        repo=companies,
        membership_repo=FakeMembershipRepo(),
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    ).execute(**_create_kwargs(actor_user_id=None))
    svc = UpdateCompanyService(repo=companies, clock=Clock())
    dto = await svc.execute(
        company_id=created.id,
        legal_name="Nova s.r.o.",
        trading_name=None,
        tax_identifier=None,
        email=None,
        phone=None,
        website_url=None,
        address_line_1=None,
        address_line_2=None,
        city=None,
        postal_code=None,
        latitude=None,
        longitude=None,
        actor_user_id=None,
    )
    assert dto.legal_name == "Nova s.r.o."


@pytest.mark.asyncio
async def test_update_company_missing():
    svc = UpdateCompanyService(repo=FakeCompanyRepo(), clock=Clock())
    with pytest.raises(NotFoundDomainError):
        await svc.execute(
            company_id=uuid4(),
            legal_name="X",
            trading_name=None,
            tax_identifier=None,
            email=None,
            phone=None,
            website_url=None,
            address_line_1=None,
            address_line_2=None,
            city=None,
            postal_code=None,
            latitude=None,
            longitude=None,
            actor_user_id=None,
        )
