from __future__ import annotations

import pytest

from app.modules.prediction.application.database_extractor import (
    DatabaseFeatureExtractor,
)
from app.modules.prediction.application.features import (
    FeatureEngine,
)
from app.modules.prediction.application.pipeline import (
    PredictionPipeline,
)
from app.modules.prediction.application.providers import (
    create_default_provider_registry,
)
from app.modules.prediction.domain.model import (
    PredictionKind,
)


class Repository:
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
        return 100

    async def inquiry_count(
        self,
        listing_id: str,
    ) -> int:
        return 4

    async def recommendation_count(
        self,
        listing_id: str,
    ) -> int:
        return 5

    async def event_count(
        self,
        listing_id: str,
    ) -> int:
        return 7

    async def company_listing_count(
        self,
        company_id: str | None,
    ) -> int:
        return 2


@pytest.mark.asyncio
async def test_full_feature_to_baseline_pipeline() -> None:
    extractor = DatabaseFeatureExtractor(Repository())

    engine = FeatureEngine(extractor)

    providers = create_default_provider_registry()

    pipeline = PredictionPipeline(
        feature_engine=engine,
        providers=providers,
        provider_name="baseline",
    )

    result = await pipeline.predict(
        subject_type="listing",
        subject_id="listing-1",
        context={
            "material_match": True,
            "location_match": True,
            "distance_km": 20,
        },
        kind=PredictionKind.INTEREST,
    )

    assert result.available
    assert result.probability is not None
    assert 0.0 <= result.probability <= 1.0
    assert result.provider == "baseline"
