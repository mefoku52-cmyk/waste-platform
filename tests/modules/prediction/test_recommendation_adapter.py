from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.modules.prediction.application.recommendation_adapter import (
    RecommendationPredictionAdapter,
    RecommendationPredictionContext,
)
from app.modules.prediction.application.recommendation_composer import (
    RecommendationScoreComposer,
)
from app.modules.prediction.application.recommendation_config import (
    RecommendationPredictionConfig,
)
from app.modules.prediction.domain.types import (
    PredictionAvailability,
    PredictionStatus,
)


@dataclass
class FakePrediction:
    score: float | None
    status: PredictionStatus
    confidence: float | None = None


class FakePredictionProvider:
    name = "fake"

    def __init__(self, result):
        self.result = result
        self.received = None

    @property
    def availability(self):
        return PredictionAvailability.ACTIVE

    async def predict(self, request):
        self.received = request
        return self.result


@pytest.mark.asyncio
async def test_adapter_works_without_prediction_provider() -> None:
    adapter = RecommendationPredictionAdapter(
        base_scorer=lambda candidate: 0.75,
    )

    result = await adapter.score(
        {"id": "listing-1"},
    )

    assert result.base_score == 0.75
    assert result.final_score == 0.75
    assert result.prediction_applied is False


@pytest.mark.asyncio
async def test_adapter_uses_prediction_when_available() -> None:
    provider = FakePredictionProvider(
        FakePrediction(
            score=0.50,
            status=PredictionStatus.AVAILABLE,
            confidence=0.90,
        )
    )

    composer = RecommendationScoreComposer(
        RecommendationPredictionConfig(
            base_weight=0.80,
            prediction_weight=0.20,
        )
    )

    adapter = RecommendationPredictionAdapter(
        base_scorer=lambda candidate: 0.80,
        prediction_provider=provider,
        composer=composer,
    )

    context = RecommendationPredictionContext(
        subject_type="listing",
        subject_id="listing-1",
        context={
            "listing_views": 20,
            "inquiry_count": 3,
        },
    )

    result = await adapter.score(
        {"id": "listing-1"},
        prediction_context=context,
    )

    assert provider.received is not None
    assert provider.received.subject_type == "listing"
    assert provider.received.subject_id == "listing-1"
    assert provider.received.context["listing_views"] == 20

    assert result.base_score == 0.80
    assert result.prediction_score == 0.50
    assert result.final_score == pytest.approx(0.74)
    assert result.prediction_applied is True


@pytest.mark.asyncio
async def test_unavailable_prediction_does_not_change_score() -> None:
    provider = FakePredictionProvider(
        FakePrediction(
            score=None,
            status=PredictionStatus.UNAVAILABLE,
        )
    )

    adapter = RecommendationPredictionAdapter(
        base_scorer=lambda candidate: 0.65,
        prediction_provider=provider,
    )

    result = await adapter.score(
        {"id": "listing-1"},
        prediction_context=RecommendationPredictionContext(
            subject_type="listing",
            subject_id="listing-1",
            context={"listing_views": 10},
        ),
    )

    assert result.base_score == 0.65
    assert result.final_score == 0.65
    assert result.prediction_applied is False
