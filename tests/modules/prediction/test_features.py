from __future__ import annotations

import pytest

from app.modules.prediction.application.baseline_extractor import (
    BaselineFeatureExtractor,
)
from app.modules.prediction.application.feature_builder import (
    FeatureBuilder,
)
from app.modules.prediction.application.features import FeatureEngine
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.features import FeatureType


def test_feature_builder_creates_typed_features() -> None:
    features = (
        FeatureBuilder(
            subject_type="listing",
            subject_id="listing-1",
        )
        .numeric(
            FeatureNames.LISTING_VIEWS,
            42,
            source="test",
        )
        .boolean(
            FeatureNames.MATERIAL_MATCH,
            True,
            source="test",
        )
        .categorical(
            FeatureNames.MATERIAL_TYPE,
            "wood",
            source="test",
        )
        .build()
    )

    assert features.subject_type == "listing"
    assert features.subject_id == "listing-1"
    assert features.value(FeatureNames.LISTING_VIEWS) == 42
    assert features.value(FeatureNames.MATERIAL_MATCH) is True
    assert features.value(FeatureNames.MATERIAL_TYPE) == "wood"
    listing_views = features.get(FeatureNames.LISTING_VIEWS)
    assert listing_views is not None
    assert listing_views.feature_type == FeatureType.NUMERIC


@pytest.mark.asyncio
async def test_baseline_extractor_normalizes_context() -> None:
    extractor = BaselineFeatureExtractor()

    features = await extractor.extract(
        subject_type="listing",
        subject_id="listing-1",
        context={
            "material_type": "wood",
            "category": "wood",
            "location": "Presov",
            "listing_views": 50,
            "inquiry_count": 4,
            "material_match": True,
            "location_match": False,
            "distance_km": 43,
        },
    )

    assert features.value(FeatureNames.MATERIAL_TYPE) == "wood"
    assert features.value(FeatureNames.LISTING_VIEWS) == 50
    assert features.value(FeatureNames.INQUIRY_COUNT) == 4
    assert features.value(FeatureNames.MATERIAL_MATCH) is True
    assert features.value(FeatureNames.LOCATION_MATCH) is False
    assert features.value(FeatureNames.DISTANCE_KM) == 43
    assert features.value(FeatureNames.DATA_COMPLETENESS) == 1.0


@pytest.mark.asyncio
async def test_feature_engine_uses_extractor_boundary() -> None:
    engine = FeatureEngine(BaselineFeatureExtractor())

    features = await engine.extract(
        subject_type="listing",
        subject_id="listing-2",
        context={
            "listing_views": 10,
        },
    )

    assert engine.extractor_name == "baseline-context"
    assert features.value(FeatureNames.LISTING_VIEWS) == 10

    # Completeness is defined against five required baseline fields:
    # material_type, category, location, listing_views, inquiry_count.
    assert features.value(FeatureNames.DATA_COMPLETENESS) == 0.2


@pytest.mark.asyncio
async def test_missing_values_do_not_create_fake_signal() -> None:
    extractor = BaselineFeatureExtractor()

    features = await extractor.extract(
        subject_type="listing",
        subject_id="listing-3",
        context={},
    )

    assert features.value(FeatureNames.LISTING_VIEWS) == 0
    assert features.value(FeatureNames.INQUIRY_COUNT) == 0
    assert features.value(FeatureNames.MATERIAL_MATCH) is False
    assert features.value(FeatureNames.DATA_COMPLETENESS) == 0.0
