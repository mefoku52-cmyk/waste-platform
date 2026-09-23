from __future__ import annotations

from app.modules.prediction.application.recommendation_config import (
    RecommendationPredictionConfig,
)
from app.modules.prediction.domain.recommendation_score import (
    CombinedRecommendationScore,
)


class RecommendationScoreComposer:
    """
    Combines the existing recommendation score with an optional prediction.

    Important behavior:

    1. Prediction unavailable:
       final_score == base_score

    2. Prediction available but below confidence threshold:
       final_score == base_score

    3. Prediction available and accepted:
       weighted combination is used.

    This makes prediction an optional capability instead of a dependency.
    """

    def __init__(
        self,
        config: RecommendationPredictionConfig | None = None,
    ) -> None:
        self._config = config or RecommendationPredictionConfig()

    def compose(
        self,
        *,
        base_score: float,
        prediction_score: float | None = None,
        prediction_confidence: float | None = None,
        prediction_available: bool = False,
    ) -> CombinedRecommendationScore:
        self._validate_score(base_score, "base_score")

        if prediction_score is not None:
            self._validate_score(prediction_score, "prediction_score")

        if prediction_confidence is not None:
            self._validate_score(
                prediction_confidence,
                "prediction_confidence",
            )

        if not prediction_available:
            return CombinedRecommendationScore(
                base_score=base_score,
                prediction_score=None,
                final_score=base_score,
                prediction_applied=False,
            )

        if prediction_score is None:
            return CombinedRecommendationScore(
                base_score=base_score,
                prediction_score=None,
                final_score=base_score,
                prediction_applied=False,
            )

        if (
            prediction_confidence is not None
            and prediction_confidence < self._config.minimum_prediction_confidence
        ):
            return CombinedRecommendationScore(
                base_score=base_score,
                prediction_score=prediction_score,
                final_score=base_score,
                prediction_applied=False,
            )

        final_score = (
            base_score * self._config.base_weight
            + prediction_score * self._config.prediction_weight
        )

        final_score = max(0.0, min(1.0, final_score))

        return CombinedRecommendationScore(
            base_score=base_score,
            prediction_score=prediction_score,
            final_score=final_score,
            prediction_applied=True,
        )

    @staticmethod
    def _validate_score(value: float, name: str) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")
