from __future__ import annotations

import pytest

from app.modules.prediction.application.baseline_evaluation import (
    evaluate_binary_predictions,
)


def test_binary_evaluation() -> None:
    result = evaluate_binary_predictions(
        predictions=[
            0.9,
            0.1,
            0.8,
            0.2,
        ],
        targets=[
            1,
            0,
            1,
            0,
        ],
    )

    assert result.count == 4
    assert result.brier_score >= 0.0
    assert result.mean_absolute_error >= 0.0
    assert result.accuracy_at_0_5 == 1.0


def test_evaluation_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError):
        evaluate_binary_predictions(
            predictions=[1.5],
            targets=[1],
        )


def test_evaluation_rejects_invalid_target() -> None:
    with pytest.raises(ValueError):
        evaluate_binary_predictions(
            predictions=[0.5],
            targets=[2],
        )


def test_evaluation_rejects_different_lengths() -> None:
    with pytest.raises(ValueError):
        evaluate_binary_predictions(
            predictions=[0.5],
            targets=[],
        )
