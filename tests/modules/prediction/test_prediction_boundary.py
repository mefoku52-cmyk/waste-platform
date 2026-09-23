from __future__ import annotations

import pytest

from app.modules.prediction.application.baseline_provider import (
    BaselinePredictionProvider,
)
from app.modules.prediction.application.config import PredictionConfig
from app.modules.prediction.application.entitlements import (
    DisabledPredictionEntitlementProvider,
)
from app.modules.prediction.application.null_provider import (
    DisabledPredictionProvider,
)
from app.modules.prediction.application.service import PredictionService
from app.modules.prediction.domain.types import (
    PredictionAvailability,
    PredictionRequest,
    PredictionStatus,
)


@pytest.mark.asyncio
async def test_disabled_provider_never_returns_zero_prediction() -> None:
    provider = DisabledPredictionProvider()

    result = await provider.predict(
        PredictionRequest(
            subject_type="listing",
            subject_id="listing-1",
            context={},
        )
    )

    assert result.status == PredictionStatus.DISABLED
    assert result.score is None
    assert provider.availability == PredictionAvailability.DISABLED


@pytest.mark.asyncio
async def test_baseline_provider_reports_unavailable_result_without_fake_score() -> None:
    provider = BaselinePredictionProvider()

    result = await provider.predict(
        PredictionRequest(
            subject_type="listing",
            subject_id="listing-1",
            context={},
        )
    )

    assert result.status == PredictionStatus.UNAVAILABLE
    assert result.score is None
    assert provider.availability == PredictionAvailability.ACTIVE


@pytest.mark.asyncio
async def test_service_disabled_is_distinct_from_not_entitled() -> None:
    entitlement = DisabledPredictionEntitlementProvider()

    service = PredictionService(
        provider=BaselinePredictionProvider(),
        entitlement_provider=entitlement,
        config=PredictionConfig(service_enabled=False),
    )

    result = await service.predict(
        principal_id="user-1",
        request=PredictionRequest(
            subject_type="listing",
            subject_id="listing-1",
            context={},
        ),
    )

    assert result.status == PredictionStatus.DISABLED
    assert result.score is None


@pytest.mark.asyncio
async def test_enabled_service_without_entitlement_is_not_entitled() -> None:
    entitlement = DisabledPredictionEntitlementProvider()

    service = PredictionService(
        provider=BaselinePredictionProvider(),
        entitlement_provider=entitlement,
        config=PredictionConfig(service_enabled=True),
    )

    result = await service.predict(
        principal_id="user-1",
        request=PredictionRequest(
            subject_type="listing",
            subject_id="listing-1",
            context={},
        ),
    )

    assert result.status == PredictionStatus.NOT_ENTITLED
    assert result.score is None


@pytest.mark.asyncio
async def test_access_reports_separate_service_and_entitlement_states() -> None:
    entitlement = DisabledPredictionEntitlementProvider()

    service = PredictionService(
        provider=BaselinePredictionProvider(),
        entitlement_provider=entitlement,
        config=PredictionConfig(service_enabled=True),
    )

    access = await service.access(
        principal_id="user-1",
    )

    assert access.service_enabled is True
    assert access.entitled is False
    assert access.provider_available is True
