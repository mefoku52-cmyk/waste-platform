from __future__ import annotations

import pytest

from app.modules.prediction.application.baseline_extractor import (
    BaselineFeatureExtractor,
)
from app.modules.prediction.application.features import FeatureEngine
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.input import PredictionInput
from app.modules.prediction.domain.snapshot import FeatureSnapshot


@pytest.mark.asyncio
async def test_feature_pipeline_produces_prediction_input() -> None:
    engine = FeatureEngine(BaselineFeatureExtractor())

    features = await engine.extract(
        subject_type="listing",
        subject_id="listing-99",
        context={
            "material_type": "metal",
            "listing_views": 100,
            "inquiry_count": 7,
            "material_match": True,
        },
    )

    snapshot = FeatureSnapshot.create(
        features=features,
        extractor=engine.extractor_name,
    )

    prediction_input = PredictionInput(
        snapshot=snapshot,
    )

    assert prediction_input.features.subject_id == "listing-99"

    assert prediction_input.features.value(FeatureNames.LISTING_VIEWS) == 100

    assert prediction_input.features.value(FeatureNames.INQUIRY_COUNT) == 7

    assert prediction_input.features.value(FeatureNames.MATERIAL_MATCH) is True
