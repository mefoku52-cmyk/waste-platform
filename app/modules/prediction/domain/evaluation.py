from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionEvaluation:
    """
    Evaluation result for a prediction.

    predicted:
        Model/provider prediction.

    actual:
        Observed outcome when it becomes available.

    error:
        Optional numeric error metric.

    metric:
        Name of the evaluation metric.
    """

    predicted: float
    actual: float
    error: float | None = None
    metric: str | None = None


def absolute_error(
    *,
    predicted: float,
    actual: float,
) -> float:
    return round(abs(predicted - actual), 12)


def evaluate_regression(
    *,
    predicted: float,
    actual: float,
) -> PredictionEvaluation:
    error = absolute_error(
        predicted=predicted,
        actual=actual,
    )

    return PredictionEvaluation(
        predicted=predicted,
        actual=actual,
        error=error,
        metric="absolute_error",
    )
