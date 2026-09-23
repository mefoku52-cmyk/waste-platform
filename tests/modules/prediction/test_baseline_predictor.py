from __future__ import annotations

from app.modules.prediction.application.baseline_config import (
    BaselineConfig,
)
from app.modules.prediction.application.baseline_predictor import (
    BaselinePredictor,
)
from app.modules.prediction.domain.feature_names import FeatureNames
from app.modules.prediction.domain.features import (
    FeatureSet,
    FeatureType,
    FeatureValue,
)
from app.modules.prediction.domain.model import (
    PredictionConfidence,
    PredictionKind,
)


def make_features(
    values: dict[str, object],
) -> FeatureSet:
    items = []

    for name, value in values.items():
        if isinstance(value, bool):
            feature_type = FeatureType.BOOLEAN
        elif isinstance(value, (int, float)):
            feature_type = FeatureType.NUMERIC
        else:
            feature_type = FeatureType.CATEGORICAL

        items.append(
            FeatureValue(
                name=name,
                value=value,
                feature_type=feature_type,
                source="test",
            )
        )

    return FeatureSet(
        subject_type="listing",
        subject_id="listing-test",
        features=tuple(items),
    )


def test_baseline_returns_available_result() -> None:
    predictor = BaselinePredictor()

    features = make_features(
        {
            FeatureNames.LISTING_VIEWS: 100,
            FeatureNames.INQUIRY_COUNT: 5,
            FeatureNames.RECOMMENDATION_COUNT: 10,
            FeatureNames.LISTING_CLICKS: 20,
            FeatureNames.MATERIAL_MATCH: True,
            FeatureNames.LOCATION_MATCH: True,
            FeatureNames.DATA_COMPLETENESS: 1.0,
        }
    )

    result = predictor.predict(
        subject_type="listing",
        subject_id="listing-test",
        features=features,
        kind=PredictionKind.INTEREST,
    )

    assert result.available is True
    assert result.probability is not None
    assert 0.0 <= result.probability <= 1.0
    assert result.provider == "baseline"
    assert result.model_version == "baseline-1"


def test_baseline_does_not_return_probability_without_evidence() -> None:
    predictor = BaselinePredictor(BaselineConfig(minimum_evidence=1))

    features = FeatureSet(
        subject_type="listing",
        subject_id="empty",
        features=(),
    )

    result = predictor.predict(
        subject_type="listing",
        subject_id="empty",
        features=features,
    )

    assert result.available is False
    assert result.probability is None
    assert result.confidence == (PredictionConfidence.UNKNOWN)


def test_baseline_probability_is_bounded() -> None:
    predictor = BaselinePredictor()

    features = make_features(
        {
            FeatureNames.LISTING_VIEWS: 1000000,
            FeatureNames.INQUIRY_COUNT: 1000000,
            FeatureNames.RECOMMENDATION_COUNT: 1000000,
            FeatureNames.LISTING_CLICKS: 1000000,
            FeatureNames.MATERIAL_MATCH: True,
            FeatureNames.LOCATION_MATCH: True,
            FeatureNames.DATA_COMPLETENESS: 1.0,
        }
    )

    result = predictor.predict(
        subject_type="listing",
        subject_id="listing-large",
        features=features,
    )

    assert result.available
    assert result.probability is not None
    assert 0.0 <= result.probability <= 1.0
