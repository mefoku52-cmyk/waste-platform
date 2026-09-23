from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.modules.prediction.domain.features import FeatureSet


@dataclass(frozen=True)
class FeatureSnapshot:
    """
    Immutable snapshot of the features used for a prediction.

    This becomes important later for model evaluation.

    If a prediction says 0.73 today, we need to know which inputs
    produced 0.73. Otherwise historical evaluation becomes guesswork.
    """

    subject_type: str
    subject_id: str
    captured_at: datetime
    features: FeatureSet
    extractor: str

    @classmethod
    def create(
        cls,
        *,
        features: FeatureSet,
        extractor: str,
    ) -> FeatureSnapshot:
        return cls(
            subject_type=features.subject_type,
            subject_id=features.subject_id,
            captured_at=datetime.now(UTC),
            features=features,
            extractor=extractor,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "captured_at": self.captured_at.isoformat(),
            "extractor": self.extractor,
            "features": self.features.as_dict(),
            "sources": self.features.source_map(),
        }
