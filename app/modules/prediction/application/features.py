from __future__ import annotations

from typing import Any

from app.modules.prediction.domain.extractor import FeatureExtractor
from app.modules.prediction.domain.features import FeatureSet


class FeatureEngine:
    """
    Application service responsible for producing normalized features.

    Prediction providers depend on FeatureSet, not on this concrete
    implementation.

    This gives us a second clean boundary:

        CMEP data
            ↓
        FeatureEngine
            ↓
        FeatureSet
            ↓
        PredictionProvider
    """

    def __init__(
        self,
        extractor: FeatureExtractor,
    ) -> None:
        self._extractor = extractor

    @property
    def extractor_name(self) -> str:
        return self._extractor.name

    async def extract(
        self,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any],
    ) -> FeatureSet:
        return await self._extractor.extract(
            subject_type=subject_type,
            subject_id=subject_id,
            context=context,
        )
