from __future__ import annotations

from app.modules.prediction.application.baseline_extractor import (
    BaselineFeatureExtractor,
)
from app.modules.prediction.application.baseline_predictor import (
    BaselinePredictor,
)
from app.modules.prediction.domain.provider import PredictionProvider
from app.modules.prediction.domain.types import (
    PredictionAvailability,
    PredictionRequest,
    PredictionResult,
    PredictionStatus,
)


class BaselinePredictionProvider(PredictionProvider):
    """
    Domain-level provider adapter for the deterministic baseline predictor.

    BaselinePredictor owns the feature-based calculation.
    This class owns the stable PredictionProvider boundary and prevents
    an empty request from being interpreted as real evidence.
    """

    def __init__(
        self,
        predictor: BaselinePredictor | None = None,
    ) -> None:
        self._predictor = predictor or BaselinePredictor()
        self._extractor = BaselineFeatureExtractor()

    @property
    def name(self) -> str:
        return "baseline"

    @property
    def availability(self) -> PredictionAvailability:
        return PredictionAvailability.ACTIVE

    async def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResult:
        if not self._has_input_signal(request.context):
            return PredictionResult(
                status=PredictionStatus.UNAVAILABLE,
                score=None,
                confidence=None,
                factors=(),
                provider=self.name,
                metadata={
                    "reason": "insufficient_input",
                },
            )

        features = await self._extractor.extract(
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            context=request.context,
        )

        result = self._predictor.predict(
            subject_type=request.subject_type,
            subject_id=request.subject_id,
            features=features,
        )

        if not result.available:
            return PredictionResult(
                status=PredictionStatus.UNAVAILABLE,
                score=None,
                confidence=result.confidence.value,
                factors=tuple(factor.name for factor in result.factors),
                provider=self.name,
                metadata=result.metadata,
            )

        return PredictionResult(
            status=PredictionStatus.AVAILABLE,
            score=result.probability,
            confidence=result.confidence.value,
            factors=tuple(factor.name for factor in result.factors),
            provider=self.name,
            metadata={
                **result.metadata,
                "model_version": result.model_version,
            },
        )

    @staticmethod
    def _has_input_signal(
        context: dict[str, object],
    ) -> bool:
        """
        Distinguish an actually empty request from legitimate zero values.

        A value of 0 is valid evidence. An absent field is not.
        """

        return bool(context)
