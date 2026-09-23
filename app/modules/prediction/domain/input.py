from __future__ import annotations

from dataclasses import dataclass

from app.modules.prediction.domain.features import FeatureSet
from app.modules.prediction.domain.snapshot import FeatureSnapshot


@dataclass(frozen=True)
class PredictionInput:
    """
    Complete input handed to a prediction implementation.

    Keeping the snapshot here ensures the model can later be evaluated
    against the exact features used at prediction time.
    """

    snapshot: FeatureSnapshot

    @property
    def features(self) -> FeatureSet:
        return self.snapshot.features
