from __future__ import annotations

from app.modules.prediction.application.baseline_provider import (
    BaselinePredictionProvider,
)
from app.modules.prediction.application.config import PredictionConfig
from app.modules.prediction.application.entitlements import (
    DisabledPredictionEntitlementProvider,
)
from app.modules.prediction.application.service import PredictionService


def create_prediction_service() -> PredictionService:
    """
    Create the safe default prediction service.

    The concrete provider can later be replaced here by:

        MLPredictionProvider
        RemotePredictionProvider
        LocalModelProvider
        ...

    without changing CMEP consumers.
    """

    config = PredictionConfig.from_environment()

    provider = BaselinePredictionProvider()
    entitlement_provider = DisabledPredictionEntitlementProvider()

    return PredictionService(
        provider=provider,
        entitlement_provider=entitlement_provider,
        config=config,
    )
