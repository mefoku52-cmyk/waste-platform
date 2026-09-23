from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.prediction.application.target_builder import (
    build_binary_target,
    make_window,
)
from app.modules.prediction.domain.outcome import (
    OutcomeEvent,
    OutcomeKind,
    TargetDefinition,
)


def test_positive_target_requires_declared_event_kind() -> None:
    prediction_time = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )

    events = (
        OutcomeEvent(
            subject_type="listing",
            subject_id="listing-1",
            kind=OutcomeKind.VIEW,
            occurred_at=prediction_time + timedelta(days=1),
        ),
        OutcomeEvent(
            subject_type="listing",
            subject_id="listing-1",
            kind=OutcomeKind.INQUIRY,
            occurred_at=prediction_time + timedelta(days=2),
        ),
    )

    definition = TargetDefinition(
        name="inquiry_7d",
        positive_kind=OutcomeKind.INQUIRY,
        horizon_days=7,
    )

    target = build_binary_target(
        events=events,
        definition=definition,
        prediction_time=prediction_time,
    )

    assert target == 1


def test_view_does_not_become_inquiry_target() -> None:
    prediction_time = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )

    events = (
        OutcomeEvent(
            subject_type="listing",
            subject_id="listing-1",
            kind=OutcomeKind.VIEW,
            occurred_at=prediction_time + timedelta(days=1),
        ),
    )

    definition = TargetDefinition(
        name="inquiry_7d",
        positive_kind=OutcomeKind.INQUIRY,
        horizon_days=7,
    )

    target = build_binary_target(
        events=events,
        definition=definition,
        prediction_time=prediction_time,
    )

    assert target == 0


def test_temporal_windows_do_not_overlap() -> None:
    prediction_time = datetime(
        2026,
        9,
        10,
        tzinfo=UTC,
    )

    history, target = make_window(
        prediction_time=prediction_time,
        history_days=30,
        target_days=7,
    )

    assert history.end == prediction_time
    assert target.start == prediction_time
    assert history.end == target.start
    assert history.start < history.end
    assert target.start < target.end
