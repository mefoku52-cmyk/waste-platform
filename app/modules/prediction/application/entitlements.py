from __future__ import annotations

import os

from app.modules.prediction.domain.entitlement import (
    PredictionEntitlementProvider,
)


class DisabledPredictionEntitlementProvider(PredictionEntitlementProvider):
    """
    Safe default until CMEP's real entitlement system is connected.

    No user receives prediction access through this adapter.

    This prevents accidental exposure while the actual subscription
    implementation is still being identified and integrated.
    """

    async def has_prediction_access(
        self,
        *,
        principal_id: str,
        company_id: str | None = None,
    ) -> bool:
        return False


class EnvironmentPredictionEntitlementProvider(PredictionEntitlementProvider):
    """Phase 3 gate until a billing module exists."""

    async def has_prediction_access(
        self,
        *,
        principal_id: str,
        company_id: str | None = None,
    ) -> bool:
        raw = os.getenv("PREDICTION_ENTITLEMENT_GRANTED", "false")
        return raw.strip().lower() in {"1", "true", "yes", "on"}


class DatabasePredictionEntitlementProvider(PredictionEntitlementProvider):
    """Reads company subscription_tier from the database.

    PRO or AI tier => prediction access.
    FREE or unknown => no access.

    Requires a CompanyEntitlementService instance.
    Never raises on missing company.
    """

    def __init__(self, *, company_entitlement_service) -> None:
        self._company_entitlements = company_entitlement_service

    async def has_prediction_access(
        self,
        *,
        principal_id: str,
        company_id: str | None = None,
    ) -> bool:
        if not company_id:
            return False
        try:
            return await self._company_entitlements.has_tier(
                str(company_id),
                _min_tier(),
            )
        except Exception:
            return False


def _min_tier():
    from app.modules.companies.domain.enums import SubscriptionTier

    return SubscriptionTier.PRO
