from __future__ import annotations

from dataclasses import dataclass

from app.modules.prediction.application.config import PredictionConfig
from app.modules.prediction.domain.entitlement import (
    PredictionEntitlementProvider,
)
from app.modules.prediction.domain.provider import PredictionProvider
from app.modules.prediction.domain.types import (
    PredictionRequest,
    PredictionResult,
    PredictionStatus,
)


@dataclass(frozen=True)
class PredictionAccess:
    """
    Resolved access state.

    This makes the distinction explicit:

        disabled
        not entitled
        unavailable
        active
    """

    service_enabled: bool
    entitled: bool
    provider_available: bool


class PredictionService:
    """
    Application-level prediction boundary.

    Order of checks:

        1. Is prediction globally enabled?
        2. Is the principal entitled?
        3. Is the provider available?
        4. Only then execute prediction.

    This keeps service availability separate from subscription state.
    """

    def __init__(
        self,
        *,
        provider: PredictionProvider,
        entitlement_provider: PredictionEntitlementProvider,
        config: PredictionConfig,
    ) -> None:
        self._provider = provider
        self._entitlement_provider = entitlement_provider
        self._config = config

    async def access(
        self,
        *,
        principal_id: str,
        company_id: str | None = None,
    ) -> PredictionAccess:
        entitled = False

        if self._config.service_enabled:
            entitled = await self._entitlement_provider.has_prediction_access(
                principal_id=principal_id,
                company_id=company_id,
            )

        return PredictionAccess(
            service_enabled=self._config.service_enabled,
            entitled=entitled,
            provider_available=(self._provider.availability.value == "active"),
        )

    async def predict(
        self,
        *,
        principal_id: str,
        request: PredictionRequest,
        company_id: str | None = None,
    ) -> PredictionResult:
        if not self._config.service_enabled:
            return PredictionResult(
                status=PredictionStatus.DISABLED,
                provider="prediction-service",
            )

        entitled = await self._entitlement_provider.has_prediction_access(
            principal_id=principal_id,
            company_id=company_id,
        )

        if not entitled:
            return PredictionResult(
                status=PredictionStatus.NOT_ENTITLED,
                provider="prediction-service",
            )

        if self._provider.availability.value != "active":
            return PredictionResult(
                status=PredictionStatus.UNAVAILABLE,
                provider=self._provider.name,
            )

        return await self._provider.predict(request)
