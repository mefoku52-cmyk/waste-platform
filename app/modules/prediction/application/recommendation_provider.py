from __future__ import annotations

from typing import Any

from app.modules.prediction.application.recommendation_adapter import (
    RecommendationPredictionAdapter,
    RecommendationPredictionContext,
)
from app.modules.prediction.domain.recommendation_score import (
    CombinedRecommendationScore,
)


class PredictionRecommendationProvider:
    """
    Application facade for optional prediction enrichment.

    It delegates all prediction semantics to RecommendationPredictionAdapter.
    """

    def __init__(
        self,
        adapter: RecommendationPredictionAdapter,
    ) -> None:
        self._adapter = adapter

    async def score(
        self,
        candidate: Any,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any],
    ) -> CombinedRecommendationScore:
        return await self._adapter.score(
            candidate,
            prediction_context=RecommendationPredictionContext(
                subject_type=subject_type,
                subject_id=subject_id,
                context=context,
            ),
        )
