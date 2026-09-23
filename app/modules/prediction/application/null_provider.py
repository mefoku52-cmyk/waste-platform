from __future__ import annotations

from app.modules.prediction.domain.provider import PredictionProvider
from app.modules.prediction.domain.types import (
    PredictionAvailability,
    PredictionRequest,
    PredictionResult,
    PredictionStatus,
)


class DisabledPredictionProvider(PredictionProvider):
    """
    Safe provider used when prediction is globally disabled.

    This is intentionally a real provider object rather than scattered
    `if prediction_enabled` checks throughout CMEP.

    Core code can therefore depend on PredictionProvider while the
    implementation underneath can be replaced or disabled.
    """

    @property
    def name(self) -> str:
        return "disabled"

    @property
    def availability(self) -> PredictionAvailability:
        return PredictionAvailability.DISABLED

    async def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResult:
        return PredictionResult(
            status=PredictionStatus.DISABLED,
            score=None,
            confidence=None,
            factors=(),
            provider=self.name,
        )
