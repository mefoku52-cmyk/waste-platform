from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryEvaluation:
    """
    Basic evaluation metrics for probability predictions.

    No ranking or business decision is made here.
    """

    count: int
    brier_score: float
    mean_absolute_error: float
    accuracy_at_0_5: float


def evaluate_binary_predictions(
    predictions: list[float],
    targets: list[int],
) -> BinaryEvaluation:
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets must have equal length.")

    if not predictions:
        return BinaryEvaluation(
            count=0,
            brier_score=0.0,
            mean_absolute_error=0.0,
            accuracy_at_0_5=0.0,
        )

    for probability in predictions:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("Prediction probability must be in [0, 1].")

    for target in targets:
        if target not in (0, 1):
            raise ValueError("Binary targets must be 0 or 1.")

    count = len(predictions)

    brier = (
        sum(
            (prediction - target) ** 2
            for prediction, target in zip(predictions, targets, strict=True)
        )
        / count
    )

    mae = (
        sum(
            abs(prediction - target)
            for prediction, target in zip(predictions, targets, strict=True)
        )
        / count
    )

    accuracy = (
        sum(
            ((prediction >= 0.5 and target == 1) or (prediction < 0.5 and target == 0))
            for prediction, target in zip(predictions, targets, strict=True)
        )
        / count
    )

    return BinaryEvaluation(
        count=count,
        brier_score=brier,
        mean_absolute_error=mae,
        accuracy_at_0_5=accuracy,
    )
