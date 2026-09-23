from __future__ import annotations

from datetime import timedelta

from app.modules.prediction.domain.outcome import (
    OutcomeEvent,
    OutcomeWindow,
    TargetDefinition,
)


def build_binary_target(
    *,
    events: tuple[OutcomeEvent, ...],
    definition: TargetDefinition,
    prediction_time,
) -> int | None:
    """
    Build a binary historical target.

    Returns:

        1 -> positive outcome observed within horizon
        0 -> no positive outcome observed within horizon
        None -> target cannot be determined

    Crucially, this function only uses events matching the explicitly
    declared outcome kind.

    It does not assume that any arbitrary event is a success.
    """

    horizon_end = prediction_time + timedelta(days=definition.horizon_days)

    matching = [
        event
        for event in events
        if (
            event.kind == definition.positive_kind
            and prediction_time <= event.occurred_at < horizon_end
        )
    ]

    if matching:
        return 1

    # If events are available but none matched, this is a legitimate
    # negative observation.
    #
    # The caller remains responsible for deciding whether the
    # observation window itself is complete.
    return 0


def make_window(
    *,
    prediction_time,
    history_days: int,
    target_days: int,
) -> tuple[OutcomeWindow, OutcomeWindow]:
    """
    Split time into:

        historical feature window
        future target window

    This explicit separation is the basis for avoiding temporal
    leakage in future model training.
    """

    if history_days <= 0:
        raise ValueError("history_days must be positive.")

    if target_days <= 0:
        raise ValueError("target_days must be positive.")

    history_start = prediction_time - timedelta(days=history_days)

    history_window = OutcomeWindow(
        start=history_start,
        end=prediction_time,
    )

    target_end = prediction_time + timedelta(days=target_days)

    target_window = OutcomeWindow(
        start=prediction_time,
        end=target_end,
    )

    return (
        history_window,
        target_window,
    )
