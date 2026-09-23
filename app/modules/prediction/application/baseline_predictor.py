from __future__ import annotations

import math
from typing import Any

from app.modules.prediction.application.baseline_config import (
    BaselineConfig,
)
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.features import FeatureSet
from app.modules.prediction.domain.model import (
    PredictionConfidence,
    PredictionFactor,
    PredictionKind,
    PredictionResult,
)


def _number(
    value: Any,
) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return float(value)

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _boolean(
    value: Any,
) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {
            "true",
            "yes",
            "1",
            "y",
        }:
            return True

        if normalized in {
            "false",
            "no",
            "0",
            "n",
        }:
            return False

    return None


def _saturating_signal(
    value: float,
    scale: float,
) -> float:
    """
    Convert a non-negative count into [0, 1].

    Formula:

        x / (x + scale)

    This avoids treating 1000 views as 100x more important than
    10 views while still preserving monotonicity.
    """

    if value <= 0:
        return 0.0

    if scale <= 0:
        return 0.0

    return value / (value + scale)


def _distance_signal(
    distance_km: float,
    scale_km: float,
) -> float:
    """
    Exponential distance decay.

    0 km -> 1
    increasing distance -> approaches 0

    This is only a baseline signal. It is NOT a claim about optimal
    logistics or geographic behavior.
    """

    if distance_km < 0:
        return 0.0

    return math.exp(-distance_km / scale_km)


def _confidence(
    evidence_count: int,
    data_completeness: float,
) -> PredictionConfidence:
    if evidence_count <= 0:
        return PredictionConfidence.UNKNOWN

    if evidence_count >= 5 and data_completeness >= 0.75:
        return PredictionConfidence.HIGH

    if evidence_count >= 2 and data_completeness >= 0.50:
        return PredictionConfidence.MEDIUM

    return PredictionConfidence.LOW


class BaselinePredictor:
    """
    Deterministic reference predictor.

    This is intentionally NOT machine learning.

    Its purpose is to establish:

        features -> prediction -> evaluation

    before a learned model is introduced.

    The implementation is transparent and versioned so that later
    model evaluation can compare itself against this baseline.
    """

    name = "baseline"
    model_version = "baseline-1"

    def __init__(
        self,
        config: BaselineConfig | None = None,
    ) -> None:
        self._config = config or BaselineConfig()

        self._config.validate()

    def predict(
        self,
        *,
        subject_type: str,
        subject_id: str,
        features: FeatureSet,
        kind: PredictionKind = PredictionKind.INTEREST,
    ) -> PredictionResult:
        factors: list[PredictionFactor] = []

        weighted_sum = 0.0
        weight_sum = 0.0
        evidence_count = 0

        # ----------------------------------------------------
        # Views
        # ----------------------------------------------------

        views = _number(features.value(FeatureNames.LISTING_VIEWS))

        if views is not None:
            signal = _saturating_signal(
                views,
                20.0,
            )

            weight = self._config.views_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="listing_views",
                    value=views,
                    contribution=signal * weight,
                    source="feature:listing_views",
                )
            )

        # ----------------------------------------------------
        # Inquiries
        # ----------------------------------------------------

        inquiries = _number(features.value(FeatureNames.INQUIRY_COUNT))

        if inquiries is not None:
            signal = _saturating_signal(
                inquiries,
                5.0,
            )

            weight = self._config.inquiries_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="inquiry_count",
                    value=inquiries,
                    contribution=signal * weight,
                    source="feature:inquiry_count",
                )
            )

        # ----------------------------------------------------
        # Recommendations
        # ----------------------------------------------------

        recommendations = _number(features.value(FeatureNames.RECOMMENDATION_COUNT))

        if recommendations is not None:
            signal = _saturating_signal(
                recommendations,
                10.0,
            )

            weight = self._config.recommendations_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="recommendation_count",
                    value=recommendations,
                    contribution=signal * weight,
                    source="feature:recommendation_count",
                )
            )

        # ----------------------------------------------------
        # Events
        # ----------------------------------------------------

        events = _number(features.value(FeatureNames.LISTING_CLICKS))

        if events is not None:
            signal = _saturating_signal(
                events,
                10.0,
            )

            weight = self._config.events_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="attributable_events",
                    value=events,
                    contribution=signal * weight,
                    source="feature:listing_events",
                )
            )

        # ----------------------------------------------------
        # Material match
        # ----------------------------------------------------

        material_match = _boolean(features.value(FeatureNames.MATERIAL_MATCH))

        if material_match is not None:
            signal = 1.0 if material_match else 0.0

            weight = self._config.material_match_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="material_match",
                    value=material_match,
                    contribution=signal * weight,
                    source="feature:material_match",
                )
            )

        # ----------------------------------------------------
        # Location match
        # ----------------------------------------------------

        location_match = _boolean(features.value(FeatureNames.LOCATION_MATCH))

        if location_match is not None:
            signal = 1.0 if location_match else 0.0

            weight = self._config.location_match_weight

            weighted_sum += signal * weight
            weight_sum += weight
            evidence_count += 1

            factors.append(
                PredictionFactor(
                    name="location_match",
                    value=location_match,
                    contribution=signal * weight,
                    source="feature:location_match",
                )
            )

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance = _number(features.value(FeatureNames.DISTANCE_KM))

        if distance is not None:
            distance_signal = _distance_signal(
                distance,
                self._config.distance_scale_km,
            )

            # Distance is currently included as metadata rather
            # than a separate weighted signal. This is intentional:
            # the existing configuration does not contain a
            # distance weight yet.
            factors.append(
                PredictionFactor(
                    name="distance_decay",
                    value={
                        "distance_km": distance,
                        "signal": distance_signal,
                    },
                    contribution=None,
                    source="feature:distance_km",
                )
            )

        # ----------------------------------------------------
        # Data completeness
        # ----------------------------------------------------

        data_completeness = _number(features.value(FeatureNames.DATA_COMPLETENESS))

        if data_completeness is None:
            data_completeness = 0.0

        data_completeness = max(
            0.0,
            min(
                1.0,
                data_completeness,
            ),
        )

        # ----------------------------------------------------
        # Availability
        # ----------------------------------------------------

        if evidence_count < self._config.minimum_evidence or weight_sum <= 0:
            return PredictionResult(
                kind=kind,
                subject_type=subject_type,
                subject_id=subject_id,
                probability=None,
                confidence=PredictionConfidence.UNKNOWN,
                provider=self.name,
                model_version=self.model_version,
                available=False,
                factors=tuple(factors),
                metadata={
                    "reason": "insufficient_evidence",
                    "evidence_count": evidence_count,
                    "data_completeness": data_completeness,
                },
            )

        # ----------------------------------------------------
        # Final normalized score
        # ----------------------------------------------------

        probability = weighted_sum / weight_sum

        probability = max(
            0.0,
            min(
                1.0,
                probability,
            ),
        )

        confidence = _confidence(
            evidence_count,
            data_completeness,
        )

        return PredictionResult(
            kind=kind,
            subject_type=subject_type,
            subject_id=subject_id,
            probability=probability,
            confidence=confidence,
            provider=self.name,
            model_version=self.model_version,
            available=True,
            factors=tuple(factors),
            metadata={
                "evidence_count": evidence_count,
                "data_completeness": data_completeness,
                "weighted_inputs": weight_sum,
            },
        )
