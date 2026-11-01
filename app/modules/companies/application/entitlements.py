"""Company subscription-tier entitlement service.

Single source of truth for company tier checks.
FREE < PRO < AI.
"""

from __future__ import annotations

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import SubscriptionTier
from app.modules.companies.domain.repositories import CompanyRepository

_TIER_ORDER: dict[SubscriptionTier, int] = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.PRO: 1,
    SubscriptionTier.AI: 2,
    SubscriptionTier.AI_NAVIGATION: 3,
}


class CompanyEntitlementService:
    """Read-only entitlement checks for a company.

    Never mutates. Never raises on unknown tier.
    """

    def __init__(self, *, repository: CompanyRepository) -> None:
        self._repo = repository

    async def get_tier(self, company_id: str) -> SubscriptionTier | None:
        if not company_id:
            return None
        company: Company | None = await self._repo.get_by_id(company_id)
        if company is None:
            return None
        return company.subscription_tier

    async def has_tier(self, company_id: str, minimum: SubscriptionTier) -> bool:
        current = await self.get_tier(company_id)
        if current is None:
            return False
        return _TIER_ORDER.get(current, 0) >= _TIER_ORDER.get(minimum, 0)
