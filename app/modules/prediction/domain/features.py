from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FeatureType(str, Enum):
    """
    Supported normalized feature types.

    The prediction layer should operate on normalized features,
    not directly on SQLAlchemy models or HTTP payloads.
    """

    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    TEXT = "text"


@dataclass(frozen=True)
class FeatureValue:
    """
    One normalized feature.

    Examples:

        listing_views = 42
        inquiry_count = 4
        material_match = True
        material_type = "wood"

    The source is retained for traceability.
    """

    name: str
    value: Any
    feature_type: FeatureType
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FeatureSet:
    """
    Complete normalized feature collection for one prediction subject.

    Prediction providers consume FeatureSet instead of reaching directly
    into CMEP database models.
    """

    subject_type: str
    subject_id: str
    features: tuple[FeatureValue, ...] = ()

    def get(self, name: str) -> FeatureValue | None:
        for feature in self.features:
            if feature.name == name:
                return feature
        return None

    def value(self, name: str, default: Any = None) -> Any:
        feature = self.get(name)

        if feature is None:
            return default

        return feature.value

    def names(self) -> tuple[str, ...]:
        return tuple(feature.name for feature in self.features)

    def as_dict(self) -> dict[str, Any]:
        return {feature.name: feature.value for feature in self.features}

    def source_map(self) -> dict[str, str]:
        return {feature.name: feature.source for feature in self.features}
