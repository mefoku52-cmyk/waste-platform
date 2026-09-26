"""SetCompanySubscriptionTierService unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.companies.application.services import (
    SetCompanySubscriptionTierService,
)
from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import (
    CompanyStatus,
    CompanyType,
    SubscriptionTier,
)
from app.shared.domain.exceptions import NotFoundDomainError


class _FakeRepo:
    def __init__(self, company: Company | None) -> None:
        self.company = company
        self.updated: list[Company] = []

    async def get_by_id(self, company_id):
        return self.company

    async def update(self, company: Company) -> None:
        self.updated.append(company)


class _Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def _company(tier: SubscriptionTier = SubscriptionTier.FREE) -> Company:
    now = datetime.now(UTC)
    return Company(
        id=uuid4(),
        status=CompanyStatus.DRAFT,
        legal_name="Test s.r.o.",
        trading_name=None,
        registration_number="12345678",
        tax_identifier=None,
        vat_identifier=None,
        subscription_tier=tier,
        company_type=CompanyType.BUYER,
        email=None,
        phone=None,
        website_url=None,
        country_code="SK",
        address_line_1="Hlavna 1",
        address_line_2=None,
        city="Zilina",
        postal_code="01001",
        latitude=None,
        longitude=None,
        seller_capability=False,
        buyer_capability=True,
        logistics_capability=False,
        verification_submitted_at=None,
        verification_reviewed_at=None,
        verification_reviewed_by_user_id=None,
        verified_at=None,
        verified_by_user_id=None,
        rejected_at=None,
        rejected_by_user_id=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )


@pytest.mark.asyncio
async def test_set_tier_from_free_to_pro() -> None:
    company = _company(SubscriptionTier.FREE)
    repo = _FakeRepo(company)
    svc = SetCompanySubscriptionTierService(repo=repo, clock=_Clock())

    dto = await svc.execute(
        company_id=company.id,
        tier=SubscriptionTier.PRO,
        actor_user_id=uuid4(),
    )
    assert dto.subscription_tier == "pro"
    assert repo.updated and repo.updated[0].subscription_tier == SubscriptionTier.PRO


@pytest.mark.asyncio
async def test_set_tier_to_ai() -> None:
    company = _company(SubscriptionTier.FREE)
    repo = _FakeRepo(company)
    svc = SetCompanySubscriptionTierService(repo=repo, clock=_Clock())

    dto = await svc.execute(
        company_id=company.id,
        tier=SubscriptionTier.AI,
        actor_user_id=None,
    )
    assert dto.subscription_tier == "ai"


@pytest.mark.asyncio
async def test_set_tier_unknown_company_raises() -> None:
    repo = _FakeRepo(None)
    svc = SetCompanySubscriptionTierService(repo=repo, clock=_Clock())

    with pytest.raises(NotFoundDomainError):
        await svc.execute(
            company_id=uuid4(),
            tier=SubscriptionTier.PRO,
            actor_user_id=uuid4(),
        )
