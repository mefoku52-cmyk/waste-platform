from __future__ import annotations

from app.modules.prediction.application.feature_builder import (
    FeatureBuilder,
)
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.snapshot import FeatureSnapshot


def test_feature_snapshot_is_serializable() -> None:
    features = (
        FeatureBuilder(
            subject_type="listing",
            subject_id="listing-1",
        )
        .numeric(
            FeatureNames.LISTING_VIEWS,
            12,
            source="test",
        )
        .build()
    )

    snapshot = FeatureSnapshot.create(
        features=features,
        extractor="test",
    )

    data = snapshot.as_dict()

    assert data["subject_type"] == "listing"
    assert data["subject_id"] == "listing-1"
    assert data["extractor"] == "test"

    assert data["features"][FeatureNames.LISTING_VIEWS] == 12

    assert data["sources"][FeatureNames.LISTING_VIEWS] == "test"
