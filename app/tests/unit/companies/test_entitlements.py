"""CompanyEntitlementService unit tests – DB-backed tier checks."""

from __future__ import annotations

import pytest

from app.modules.companies.application.entitlements import (
    CompanyEntitlementService,
)
from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import (
    CompanyStatus,
    CompanyType,
    SubscriptionTier,
)


class _FakeRepo:
    def __init__(self, companies: dict[str, Company]) -> None:
        self._companies = companies

    async def get_by_id(self, company_id: str) -> Company | None:
        return self._companies.get(str(company_id))


def _company(*, id: str, tier: SubscriptionTier) -> Company:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return Company(
        id=id,
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


def _svc(*companies: Company) -> CompanyEntitlementService:
    repo = _FakeRepo({str(c.id): c for c in companies})
    return CompanyEntitlementService(repository=repo)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_tier_returns_stored_tier() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.PRO))
    assert await svc.get_tier("c1") == SubscriptionTier.PRO


@pytest.mark.asyncio
async def test_get_tier_returns_none_for_unknown_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.PRO))
    assert await svc.get_tier("missing") is None


@pytest.mark.asyncio
async def test_get_tier_returns_none_for_empty_id() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.PRO))
    assert await svc.get_tier("") is None


@pytest.mark.asyncio
async def test_has_tier_free_min_matches_free_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.FREE))
    assert await svc.has_tier("c1", SubscriptionTier.FREE) is True


@pytest.mark.asyncio
async def test_has_tier_pro_min_denies_free_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.FREE))
    assert await svc.has_tier("c1", SubscriptionTier.PRO) is False


@pytest.mark.asyncio
async def test_has_tier_pro_min_allows_pro_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.PRO))
    assert await svc.has_tier("c1", SubscriptionTier.PRO) is True


@pytest.mark.asyncio
async def test_has_tier_ai_min_denies_pro_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.PRO))
    assert await svc.has_tier("c1", SubscriptionTier.AI) is False


@pytest.mark.asyncio
async def test_has_tier_ai_min_allows_ai_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.AI))
    assert await svc.has_tier("c1", SubscriptionTier.AI) is True


@pytest.mark.asyncio
async def test_has_tier_denies_unknown_company() -> None:
    svc = _svc(_company(id="c1", tier=SubscriptionTier.AI))
    assert await svc.has_tier("missing", SubscriptionTier.FREE) is False
