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
