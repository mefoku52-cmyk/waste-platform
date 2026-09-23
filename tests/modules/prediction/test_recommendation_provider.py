from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.modules.prediction.application.recommendation_adapter import (
    RecommendationPredictionAdapter,
)
from app.modules.prediction.application.recommendation_provider import (
    PredictionRecommendationProvider,
)
from app.modules.prediction.domain.types import (
    PredictionRequest,
)


@dataclass
class FakePrediction:
    score: float | None
    status: str = "available"
    confidence: float | None = 1.0


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[PredictionRequest] = []

    async def predict(
        self,
        request: PredictionRequest,
    ) -> FakePrediction:
        self.calls.append(request)

        return FakePrediction(
            score=0.60,
        )


@pytest.mark.asyncio
async def test_provider_facade_passes_prediction_request() -> None:
    prediction = FakeProvider()

    adapter = RecommendationPredictionAdapter(
        base_scorer=lambda candidate: 0.70,
        prediction_provider=prediction,
    )

    facade = PredictionRecommendationProvider(adapter)

    context = {
        "listing_views": 12,
        "inquiry_count": 2,
    }

    result = await facade.score(
        {"id": "listing-1"},
        subject_type="listing",
        subject_id="listing-1",
        context=context,
    )

    assert len(prediction.calls) == 1

    request = prediction.calls[0]

    assert request.subject_type == "listing"
    assert request.subject_id == "listing-1"
    assert request.context == context

    assert result.base_score == 0.70
    assert result.prediction_score == 0.60
    assert result.prediction_applied is True
