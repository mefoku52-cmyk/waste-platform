from __future__ import annotations

import pytest

from app.modules.prediction.application.recommendation_composer import (
    RecommendationScoreComposer,
)
from app.modules.prediction.application.recommendation_config import (
    RecommendationPredictionConfig,
)


def test_unavailable_prediction_preserves_base_score() -> None:
    composer = RecommendationScoreComposer()

    result = composer.compose(
        base_score=0.70,
        prediction_score=None,
        prediction_available=False,
    )

    assert result.base_score == 0.70
    assert result.prediction_score is None
    assert result.final_score == 0.70
    assert result.prediction_applied is False


def test_available_prediction_is_combined() -> None:
    composer = RecommendationScoreComposer(
        RecommendationPredictionConfig(
            base_weight=0.80,
            prediction_weight=0.20,
        )
    )

    result = composer.compose(
        base_score=0.80,
        prediction_score=0.40,
        prediction_available=True,
    )

    assert result.prediction_applied is True
    assert result.final_score == pytest.approx(0.72)


def test_confidence_threshold_can_disable_prediction() -> None:
    composer = RecommendationScoreComposer(
        RecommendationPredictionConfig(
            base_weight=0.80,
            prediction_weight=0.20,
            minimum_prediction_confidence=0.70,
        )
    )

    result = composer.compose(
        base_score=0.80,
        prediction_score=0.20,
        prediction_confidence=0.40,
        prediction_available=True,
    )

    assert result.final_score == 0.80
    assert result.prediction_applied is False


def test_prediction_without_probability_is_ignored() -> None:
    composer = RecommendationScoreComposer()

    result = composer.compose(
        base_score=0.50,
        prediction_score=None,
        prediction_available=True,
    )

    assert result.final_score == 0.50
    assert result.prediction_applied is False


@pytest.mark.parametrize(
    "base_score",
    [-0.1, 1.1],
)
def test_invalid_base_score_is_rejected(base_score: float) -> None:
    composer = RecommendationScoreComposer()

    with pytest.raises(ValueError):
        composer.compose(
            base_score=base_score,
            prediction_available=False,
        )


def test_config_requires_weights_to_sum_to_one() -> None:
    with pytest.raises(ValueError):
        RecommendationPredictionConfig(
            base_weight=0.50,
            prediction_weight=0.60,
        )
