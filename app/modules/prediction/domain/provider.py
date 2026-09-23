from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.prediction.domain.types import (
    PredictionAvailability,
    PredictionRequest,
    PredictionResult,
)


class PredictionProvider(ABC):
    """
    Stable boundary between CMEP core and prediction implementation.

    The rest of CMEP should depend on this interface, never on a
    concrete ML model, library, remote API, or prediction process.

    This makes it possible to run CMEP with:

        Prediction = OFF

    without removing or breaking the rest of the platform.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider identifier."""

    @property
    @abstractmethod
    def availability(self) -> PredictionAvailability:
        """Current runtime availability."""

    @abstractmethod
    async def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResult:
        """
        Generate a prediction.

        Implementations must return a structured result and must never
        silently convert an unavailable provider into score=0.
        """
        raise NotImplementedError
