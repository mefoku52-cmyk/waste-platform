from __future__ import annotations

from typing import Any

from app.modules.prediction.application.baseline_predictor import (
    BaselinePredictor,
)
from app.modules.prediction.domain.model import (
    PredictionKind,
    PredictionResult,
)


class BaselinePipelineProvider:
    """
    Feature/model-pipeline adapter for the deterministic baseline predictor.

    This provider intentionally uses the legacy/model pipeline contract:
    an already extracted FeatureSet is passed directly to BaselinePredictor.

    The stable domain PredictionProvider boundary is implemented separately
    by BaselinePredictionProvider.
    """

    name = "baseline"

    def __init__(
        self,
        predictor: BaselinePredictor | None = None,
    ) -> None:
        self._predictor = predictor or BaselinePredictor()

    async def predict(
        self,
        *,
        subject_type: str,
        subject_id: str,
        features: Any,
        context: dict[str, Any] | None = None,
        kind: PredictionKind = PredictionKind.INTEREST,
    ) -> PredictionResult:
        return self._predictor.predict(
            subject_type=subject_type,
            subject_id=subject_id,
            features=features,
            kind=kind,
        )


__all__ = ["BaselinePipelineProvider"]
