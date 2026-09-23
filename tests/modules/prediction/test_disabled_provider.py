from __future__ import annotations

import pytest

from app.modules.prediction.application.disabled_provider import (
    DisabledPredictionProvider,
)
from app.modules.prediction.domain.features import FeatureSet


@pytest.mark.asyncio
async def test_disabled_is_not_zero_prediction() -> None:
    provider = DisabledPredictionProvider(reason="service_disabled")

    result = await provider.predict(
        subject_type="listing",
        subject_id="listing-1",
        features=FeatureSet(
            subject_type="listing",
            subject_id="listing-1",
            features=(),
        ),
    )

    assert result.available is False
    assert result.probability is None
    assert result.metadata["reason"] == ("service_disabled")
