from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationPredictionConfig:
    """
    Configuration for combining an existing recommendation score with
    an optional prediction score.

    The default is intentionally conservative:
      - 80% existing recommendation logic
      - 20% prediction

    Prediction must never replace the existing recommendation system.
    """

    base_weight: float = 0.80
    prediction_weight: float = 0.20
    minimum_prediction_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.base_weight < 0.0:
            raise ValueError("base_weight must be >= 0")

        if self.prediction_weight < 0.0:
            raise ValueError("prediction_weight must be >= 0")

        total = self.base_weight + self.prediction_weight

        if abs(total - 1.0) > 1e-9:
            raise ValueError("base_weight + prediction_weight must equal 1")

        if not 0.0 <= self.minimum_prediction_confidence <= 1.0:
            raise ValueError("minimum_prediction_confidence must be between 0 and 1")
