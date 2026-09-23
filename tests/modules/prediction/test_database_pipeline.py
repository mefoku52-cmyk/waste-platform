from __future__ import annotations

import pytest

from app.modules.prediction.application.database_extractor import (
    DatabaseFeatureExtractor,
)
from app.modules.prediction.application.features import FeatureEngine
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.snapshot import FeatureSnapshot


class PipelineRepository:
    async def get_listing(
        self,
        listing_id: str,
    ) -> dict:
        return {
            "id": listing_id,
            "material_type": "metal",
            "category": "metal",
            "location": "Kosice",
            "company_id": "company-7",
            "status": "published",
        }

    async def listing_view_count(
        self,
        listing_id: str,
    ) -> int:
        return 120

    async def inquiry_count(
        self,
        listing_id: str,
    ) -> int:
        return 9

    async def recommendation_count(
        self,
        listing_id: str,
    ) -> int:
        return 14

    async def event_count(
        self,
        listing_id: str,
    ) -> int:
        return 22

    async def company_listing_count(
        self,
        company_id: str | None,
    ) -> int:
        return 6


@pytest.mark.asyncio
async def test_database_features_create_prediction_snapshot() -> None:
    extractor = DatabaseFeatureExtractor(PipelineRepository())

    engine = FeatureEngine(extractor)

    features = await engine.extract(
        subject_type="listing",
        subject_id="listing-real",
        context={
            "distance_km": 25,
            "material_match": True,
        },
    )

    snapshot = FeatureSnapshot.create(
        features=features,
        extractor=engine.extractor_name,
    )

    assert snapshot.extractor == "cmep-database"

    assert snapshot.features.value(FeatureNames.LISTING_VIEWS) == 120

    assert snapshot.features.value(FeatureNames.INQUIRY_COUNT) == 9

    assert snapshot.features.value(FeatureNames.RECOMMENDATION_COUNT) == 14

    assert snapshot.features.value(FeatureNames.COMPANY_LISTING_COUNT) == 6

    assert snapshot.features.value(FeatureNames.DISTANCE_KM) == 25
