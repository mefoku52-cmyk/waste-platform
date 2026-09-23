from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationScore:
    """
    Deterministic recommendation score before prediction enrichment.

    `base_score` always represents the existing recommendation logic.

    `prediction_score` is optional because prediction is an enhancement,
    not a hard dependency of the CMEP recommendation system.
    """

    base_score: float
    prediction_score: float | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.base_score <= 1.0:
            raise ValueError("base_score must be between 0 and 1")

        if self.prediction_score is not None:
            if not 0.0 <= self.prediction_score <= 1.0:
                raise ValueError("prediction_score must be between 0 and 1")


@dataclass(frozen=True)
class CombinedRecommendationScore:
    """
    Result after optional prediction enrichment.

    `base_score` remains visible so that callers can distinguish the
    original recommendation score from the prediction-enhanced score.
    """

    base_score: float
    prediction_score: float | None
    final_score: float
    prediction_applied: bool

    def __post_init__(self) -> None:
        if not 0.0 <= self.base_score <= 1.0:
            raise ValueError("base_score must be between 0 and 1")

        if self.prediction_score is not None:
            if not 0.0 <= self.prediction_score <= 1.0:
                raise ValueError("prediction_score must be between 0 and 1")

        if not 0.0 <= self.final_score <= 1.0:
            raise ValueError("final_score must be between 0 and 1")
