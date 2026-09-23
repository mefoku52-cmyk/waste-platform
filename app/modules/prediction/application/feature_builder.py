from __future__ import annotations

from typing import Any

from app.modules.prediction.domain.features import (
    FeatureSet,
    FeatureType,
    FeatureValue,
)


class FeatureBuilder:
    """
    Small helper used by extractors.

    It keeps feature creation consistent and makes it harder to
    accidentally mix raw database objects with prediction features.
    """

    def __init__(
        self,
        *,
        subject_type: str,
        subject_id: str,
    ) -> None:
        self._subject_type = subject_type
        self._subject_id = subject_id
        self._features: list[FeatureValue] = []

    def add(
        self,
        *,
        name: str,
        value: Any,
        feature_type: FeatureType,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureBuilder:
        self._features.append(
            FeatureValue(
                name=name,
                value=value,
                feature_type=feature_type,
                source=source,
                metadata=metadata or {},
            )
        )

        return self

    def numeric(
        self,
        name: str,
        value: int | float,
        *,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureBuilder:
        return self.add(
            name=name,
            value=value,
            feature_type=FeatureType.NUMERIC,
            source=source,
            metadata=metadata,
        )

    def boolean(
        self,
        name: str,
        value: bool,
        *,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureBuilder:
        return self.add(
            name=name,
            value=value,
            feature_type=FeatureType.BOOLEAN,
            source=source,
            metadata=metadata,
        )

    def categorical(
        self,
        name: str,
        value: str | None,
        *,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureBuilder:
        return self.add(
            name=name,
            value=value,
            feature_type=FeatureType.CATEGORICAL,
            source=source,
            metadata=metadata,
        )

    def text(
        self,
        name: str,
        value: str | None,
        *,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> FeatureBuilder:
        return self.add(
            name=name,
            value=value,
            feature_type=FeatureType.TEXT,
            source=source,
            metadata=metadata,
        )

    def build(self) -> FeatureSet:
        return FeatureSet(
            subject_type=self._subject_type,
            subject_id=self._subject_id,
            features=tuple(self._features),
        )
