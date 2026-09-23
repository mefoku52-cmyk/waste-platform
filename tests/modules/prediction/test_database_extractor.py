from __future__ import annotations

import pytest

from app.modules.prediction.application.database_extractor import (
    DatabaseFeatureExtractor,
)
from app.modules.prediction.domain.feature_names import FeatureNames


class FakeRepository:
    async def get_listing(
        self,
        listing_id: str,
    ) -> dict:
        return {
            "id": listing_id,
            "material_type": "wood",
            "category": "wood",
            "location": "Presov",
            "company_id": "company-1",
            "status": "published",
        }

    async def listing_view_count(
        self,
        listing_id: str,
    ) -> int:
        return 50

    async def inquiry_count(
        self,
        listing_id: str,
    ) -> int:
        return 5

    async def recommendation_count(
        self,
        listing_id: str,
    ) -> int:
        return 8

    async def event_count(
        self,
        listing_id: str,
    ) -> int:
        return 12

    async def company_listing_count(
        self,
        company_id: str | None,
    ) -> int:
        return 3


@pytest.mark.asyncio
async def test_database_extractor_builds_real_feature_set() -> None:
    extractor = DatabaseFeatureExtractor(FakeRepository())

    features = await extractor.extract(
        subject_type="listing",
        subject_id="listing-1",
        context={
            "distance_km": 43,
            "material_match": True,
            "location_match": True,
        },
    )

    assert features.subject_id == "listing-1"

    assert features.value(FeatureNames.MATERIAL_TYPE) == "wood"

    assert features.value(FeatureNames.CATEGORY) == "wood"

    assert features.value(FeatureNames.LOCATION) == "Presov"

    assert features.value(FeatureNames.LISTING_VIEWS) == 50

    assert features.value(FeatureNames.INQUIRY_COUNT) == 5

    assert features.value(FeatureNames.RECOMMENDATION_COUNT) == 8

    assert features.value(FeatureNames.LISTING_CLICKS) == 12

    assert features.value(FeatureNames.COMPANY_LISTING_COUNT) == 3

    assert features.value(FeatureNames.DISTANCE_KM) == 43

    assert features.value(FeatureNames.MATERIAL_MATCH) is True

    assert features.value(FeatureNames.LOCATION_MATCH) is True


@pytest.mark.asyncio
async def test_database_extractor_does_not_fake_unknown_data() -> None:
    class EmptyRepository:
        async def get_listing(
            self,
            listing_id: str,
        ) -> dict:
            return {}

        async def listing_view_count(
            self,
            listing_id: str,
        ) -> int:
            return 0

        async def inquiry_count(
            self,
            listing_id: str,
        ) -> int:
            return 0

        async def recommendation_count(
            self,
            listing_id: str,
        ) -> int:
            return 0

        async def event_count(
            self,
            listing_id: str,
        ) -> int:
            return 0

        async def company_listing_count(
            self,
            company_id: str | None,
        ) -> int:
            return 0

    extractor = DatabaseFeatureExtractor(EmptyRepository())

    features = await extractor.extract(
        subject_type="listing",
        subject_id="listing-empty",
        context={},
    )

    assert features.value(FeatureNames.LISTING_VIEWS) == 0

    assert features.value(FeatureNames.INQUIRY_COUNT) == 0

    assert features.value(FeatureNames.RECOMMENDATION_COUNT) == 0

    assert features.value(FeatureNames.DATA_COMPLETENESS) == 0.0

    assert features.get(FeatureNames.MATERIAL_TYPE) is None
