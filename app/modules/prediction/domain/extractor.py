from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.modules.prediction.domain.features import FeatureSet


class FeatureExtractor(ABC):
    """
    Stable boundary between CMEP application data and prediction.

    Concrete implementations may later consume:

        listings
        listing_views
        inquiries
        recommendations
        analytics_events
        activity_events

    But the prediction engine receives only FeatureSet.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def extract(
        self,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any],
    ) -> FeatureSet:
        raise NotImplementedError
