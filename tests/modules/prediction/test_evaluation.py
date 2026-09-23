from __future__ import annotations

from app.modules.prediction.domain.evaluation import (
    absolute_error,
    evaluate_regression,
)


def test_absolute_error() -> None:
    assert (
        absolute_error(
            predicted=0.73,
            actual=0.81,
        )
        == 0.08
    )


def test_regression_evaluation() -> None:
    result = evaluate_regression(
        predicted=0.73,
        actual=0.81,
    )

    assert result.predicted == 0.73
    assert result.actual == 0.81
    assert result.metric == "absolute_error"
    assert result.error == 0.08
