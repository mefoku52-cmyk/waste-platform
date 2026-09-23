from __future__ import annotations

from typing import Any

from app.modules.prediction.application.feature_builder import (
    FeatureBuilder,
)
from app.modules.prediction.domain.extractor import FeatureExtractor
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.features import FeatureSet


def _number(
    value: Any,
    default: int | float = 0,
) -> int | float:
    if value is None:
        return default

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return value

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _string(
    value: Any,
    default: str | None = None,
) -> str | None:
    if value is None:
        return default

    text = str(value).strip()

    return text or default


def _bool(
    value: Any,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }

    return default


class BaselineFeatureExtractor(FeatureExtractor):
    """
    Provider-neutral first extractor.

    It accepts an already prepared context dictionary.

    This is intentional. We do NOT yet bind prediction directly to
    SQLAlchemy models until the exact existing CMEP repositories and
    services are mapped.

    Later this extractor can be replaced by a database-backed
    application extractor without changing FeatureSet consumers.
    """

    @property
    def name(self) -> str:
        return "baseline-context"

    async def extract(
        self,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any],
    ) -> FeatureSet:
        builder = FeatureBuilder(
            subject_type=subject_type,
            subject_id=subject_id,
        )

        # --------------------------------------------------------
        # Listing classification
        # --------------------------------------------------------

        material_type = _string(context.get("material_type") or context.get("materialType"))

        category = _string(context.get("category"))

        location = _string(context.get("location"))

        if material_type is not None:
            builder.categorical(
                FeatureNames.MATERIAL_TYPE,
                material_type,
                source="context",
            )

        if category is not None:
            builder.categorical(
                FeatureNames.CATEGORY,
                category,
                source="context",
            )

        if location is not None:
            builder.categorical(
                FeatureNames.LOCATION,
                location,
                source="context",
            )

        # --------------------------------------------------------
        # Activity
        # --------------------------------------------------------

        builder.numeric(
            FeatureNames.LISTING_VIEWS,
            _number(context.get("listing_views") or context.get("views")),
            source="context",
        )

        builder.numeric(
            FeatureNames.LISTING_CLICKS,
            _number(context.get("listing_clicks") or context.get("clicks")),
            source="context",
        )

        builder.numeric(
            FeatureNames.LISTING_SAVES,
            _number(context.get("listing_saves") or context.get("saves")),
            source="context",
        )

        # --------------------------------------------------------
        # Commercial activity
        # --------------------------------------------------------

        builder.numeric(
            FeatureNames.INQUIRY_COUNT,
            _number(context.get("inquiry_count") or context.get("inquiries")),
            source="context",
        )

        builder.numeric(
            FeatureNames.MATCH_COUNT,
            _number(context.get("match_count") or context.get("matches")),
            source="context",
        )

        builder.numeric(
            FeatureNames.RECOMMENDATION_COUNT,
            _number(context.get("recommendation_count") or context.get("recommendations")),
            source="context",
        )

        # --------------------------------------------------------
        # Outcomes
        # --------------------------------------------------------

        builder.numeric(
            FeatureNames.DEAL_COUNT,
            _number(context.get("deal_count") or context.get("deals")),
            source="context",
        )

        builder.numeric(
            FeatureNames.COMPLETION_COUNT,
            _number(context.get("completion_count") or context.get("completions")),
            source="context",
        )

        # --------------------------------------------------------
        # Temporal
        # --------------------------------------------------------

        builder.numeric(
            FeatureNames.DAYS_ACTIVE,
            _number(context.get("days_active")),
            source="context",
        )

        builder.numeric(
            FeatureNames.DAYS_SINCE_ACTIVITY,
            _number(context.get("days_since_activity")),
            source="context",
        )

        # --------------------------------------------------------
        # Company
        # --------------------------------------------------------

        builder.numeric(
            FeatureNames.COMPANY_ACTIVITY,
            _number(context.get("company_activity")),
            source="context",
        )

        builder.numeric(
            FeatureNames.COMPANY_LISTING_COUNT,
            _number(context.get("company_listing_count")),
            source="context",
        )

        # --------------------------------------------------------
        # Geography
        # --------------------------------------------------------

        distance = context.get("distance_km")

        if distance is not None:
            builder.numeric(
                FeatureNames.DISTANCE_KM,
                _number(distance),
                source="context",
            )

        # --------------------------------------------------------
        # Matching
        # --------------------------------------------------------

        builder.boolean(
            FeatureNames.MATERIAL_MATCH,
            _bool(context.get("material_match")),
            source="context",
        )

        builder.boolean(
            FeatureNames.LOCATION_MATCH,
            _bool(context.get("location_match")),
            source="context",
        )

        # --------------------------------------------------------
        # Data completeness
        # --------------------------------------------------------

        expected_fields = (
            "material_type",
            "category",
            "location",
            "listing_views",
            "inquiry_count",
        )

        available = sum(1 for field in expected_fields if context.get(field) is not None)

        completeness = available / len(expected_fields)

        builder.numeric(
            FeatureNames.DATA_COMPLETENESS,
            completeness,
            source="feature-engine",
        )

        return builder.build()
