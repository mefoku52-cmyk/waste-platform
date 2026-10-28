import uuid
from datetime import datetime

import pytest

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType, SubscriptionTier
from app.modules.companies.infrastructure.repositories import SqlAlchemyCompanyRepository
from app.shared.infrastructure.db.session import async_session_maker


def _company():
    now = datetime(2026, 9, 17, 10, 0, 0)
    return Company(
        id=uuid.uuid4(),
        status=CompanyStatus.DRAFT,
        legal_name="Test s.r.o.",
        trading_name=None,
        registration_number="12345678",
        tax_identifier=None,
        vat_identifier=None,
        subscription_tier=SubscriptionTier.FREE,
        company_type=CompanyType.SELLER,
        email="a@b.sk",
        phone=None,
        website_url=None,
        country_code="SK",
        address_line_1="Hlavna 1",
        address_line_2=None,
        city="BA",
        postal_code="81101",
        latitude=None,
        longitude=None,
        seller_capability=True,
        buyer_capability=False,
        logistics_capability=False,
        verification_submitted_at=None,
        verification_reviewed_at=None,
        verification_reviewed_by_user_id=None,
        verified_at=None,
        verified_by_user_id=None,
        rejected_at=None,
        rejected_by_user_id=None,
        created_at=now,
        updated_at=now,
        created_by_user_id=None,
        updated_by_user_id=None,
    )


@pytest.fixture
async def session():
    async with async_session_maker() as s:
        yield s


@pytest.mark.asyncio
async def test_company_repo_add_get(session):
    repo = SqlAlchemyCompanyRepository(session)
    c = _company()
    await repo.add(c)
    fetched = await repo.get_by_id(c.id)
    assert fetched is not None
    assert fetched.legal_name == "Test s.r.o."
    # cleanup
    await session.delete(
        await session.get(
            __import__(
                "app.modules.companies.infrastructure.models", fromlist=["CompanyModel"]
            ).CompanyModel,
            str(c.id),
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_company_repo_list(session):
    repo = SqlAlchemyCompanyRepository(session)
    c = _company()
    await repo.add(c)
    rows, total = await repo.list(q="Test", page=1, page_size=5)
    assert total >= 1
    # cleanup
    from app.modules.companies.infrastructure.models import CompanyModel

    await session.delete(await session.get(CompanyModel, str(c.id)))
    await session.commit()
