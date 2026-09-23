from __future__ import annotations

from typing import Any

from app.modules.prediction.domain.features import FeatureSet
from app.modules.prediction.domain.model import (
    PredictionConfidence,
    PredictionFactor,
    PredictionKind,
    PredictionResult,
)


class DisabledPredictionProvider:
    """
    Explicit unavailable provider.

    This is critical:

        unavailable != prediction 0

    A disabled service therefore never contaminates analytics or
    recommendation scores with artificial zero values.
    """

    name = "disabled"

    def __init__(
        self,
        *,
        reason: str = "disabled",
    ) -> None:
        self._reason = reason

    async def predict(
        self,
        *,
        subject_type: str,
        subject_id: str,
        features: FeatureSet,
        context: dict[str, Any] | None = None,
        kind: PredictionKind = PredictionKind.INTEREST,
    ) -> PredictionResult:
        del features
        del context

        return PredictionResult(
            kind=kind,
            subject_type=subject_type,
            subject_id=subject_id,
            probability=None,
            confidence=PredictionConfidence.UNKNOWN,
            provider=self.name,
            model_version="none",
            available=False,
            factors=(
                PredictionFactor(
                    name="availability",
                    value="unavailable",
                    contribution=None,
                    source="prediction-runtime",
                ),
            ),
            metadata={
                "reason": self._reason,
            },
        )
