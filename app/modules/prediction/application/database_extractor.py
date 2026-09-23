from __future__ import annotations

from typing import Any

from app.modules.prediction.application.feature_builder import (
    FeatureBuilder,
)
from app.modules.prediction.domain.extractor import FeatureExtractor
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.features import FeatureSet
from app.modules.prediction.infrastructure.database_repository import (
    PredictionDataRepository,
)


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


def _text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    return value or None


class DatabaseFeatureExtractor(FeatureExtractor):
    """
    Real CMEP database-backed feature extractor.

    Current subject:

        listing

    Current real data sources:

        listings
        listing_views
        inquiries
        recommendations, when persisted
        activity_events / events / analytics_events, when directly
        attributable to the listing

    No data is written.
    """

    def __init__(
        self,
        repository: PredictionDataRepository,
    ) -> None:
        self._repository = repository

    @property
    def name(self) -> str:
        return "cmep-database"

    async def extract(
        self,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any],
    ) -> FeatureSet:
        """
        Extract features from the actual CMEP database.

        context may contain optional request-time information such as:

            distance_km
            material_match
            location_match

        Database-owned values always come from the repository.
        """

        if subject_type != "listing":
            return FeatureSet(
                subject_type=subject_type,
                subject_id=subject_id,
                features=(),
            )

        listing = await self._repository.get_listing(subject_id)

        builder = FeatureBuilder(
            subject_type=subject_type,
            subject_id=subject_id,
        )

        # --------------------------------------------------------
        # Listing fields
        # --------------------------------------------------------

        material_type = _text(listing.get("material_type") or listing.get("materialType"))

        category = _text(listing.get("category"))

        location = _text(listing.get("location"))

        company_id = _text(listing.get("company_id") or listing.get("companyId"))

        if material_type is not None:
            builder.categorical(
                FeatureNames.MATERIAL_TYPE,
                material_type,
                source="db:listings",
            )

        if category is not None:
            builder.categorical(
                FeatureNames.CATEGORY,
                category,
                source="db:listings",
            )

        if location is not None:
            builder.categorical(
                FeatureNames.LOCATION,
                location,
                source="db:listings",
            )

        # --------------------------------------------------------
        # Listing views
        # --------------------------------------------------------

        listing_views = await self._repository.listing_view_count(subject_id)

        builder.numeric(
            FeatureNames.LISTING_VIEWS,
            listing_views,
            source="db:listing_views",
        )

        # --------------------------------------------------------
        # Inquiries
        # --------------------------------------------------------

        inquiries = await self._repository.inquiry_count(subject_id)

        builder.numeric(
            FeatureNames.INQUIRY_COUNT,
            inquiries,
            source="db:inquiries",
        )

        # --------------------------------------------------------
        # Recommendations
        # --------------------------------------------------------

        recommendations = await self._repository.recommendation_count(subject_id)

        builder.numeric(
            FeatureNames.RECOMMENDATION_COUNT,
            recommendations,
            source="db:recommendations",
        )

        # --------------------------------------------------------
        # Events
        # --------------------------------------------------------

        events = await self._repository.event_count(subject_id)

        builder.numeric(
            FeatureNames.LISTING_CLICKS,
            events,
            source="db:events",
            metadata={
                "semantic_note": ("Directly attributable event count. Not assumed to mean clicks.")
            },
        )

        # --------------------------------------------------------
        # Company activity
        # --------------------------------------------------------

        company_listing_count = await self._repository.company_listing_count(company_id)

        builder.numeric(
            FeatureNames.COMPANY_LISTING_COUNT,
            company_listing_count,
            source="db:listings",
        )

        # --------------------------------------------------------
        # Request-time matching signals
        # --------------------------------------------------------

        if "distance_km" in context:
            builder.numeric(
                FeatureNames.DISTANCE_KM,
                _number(context.get("distance_km")),
                source="request-context",
            )

        if "material_match" in context:
            builder.boolean(
                FeatureNames.MATERIAL_MATCH,
                bool(context.get("material_match")),
                source="request-context",
            )

        if "location_match" in context:
            builder.boolean(
                FeatureNames.LOCATION_MATCH,
                bool(context.get("location_match")),
                source="request-context",
            )

        # --------------------------------------------------------
        # Existing status
        # --------------------------------------------------------

        status = _text(listing.get("status"))

        if status is not None:
            builder.categorical(
                "listing_status",
                status,
                source="db:listings",
            )

        # --------------------------------------------------------
        # Data completeness
        # --------------------------------------------------------

        expected_database_signals = (
            material_type,
            category,
            location,
            listing,
        )

        available = sum(1 for value in expected_database_signals if value)

        completeness = available / len(expected_database_signals)

        builder.numeric(
            FeatureNames.DATA_COMPLETENESS,
            completeness,
            source="feature-engine",
        )

        return builder.build()
