from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class OutcomeKind(StrEnum):
    """
    Observable business outcome categories.

    These are deliberately neutral observations.

    A future target definition may select one of these as the
    supervised-learning target, but the data layer itself must
    not decide what constitutes 'success'.
    """

    VIEW = "view"
    INQUIRY = "inquiry"
    MATCH = "match"
    RESERVATION = "reservation"
    COMPLETION = "completion"
    CUSTOM = "custom"


@dataclass(frozen=True)
class OutcomeEvent:
    """
    Immutable historical observation.
    """

    subject_type: str
    subject_id: str
    kind: OutcomeKind
    occurred_at: datetime
    value: float = 1.0
    source: str = "unknown"
    event_id: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Outcome value cannot be negative.")


@dataclass(frozen=True)
class OutcomeWindow:
    """
    A bounded historical window used for evaluation/training.

    The window is explicit so future model training cannot silently
    mix observations from unrelated periods.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("OutcomeWindow.end must be after start.")


@dataclass(frozen=True)
class TargetDefinition:
    """
    Explicit definition of what a model is trying to predict.

    This prevents accidental target leakage and avoids hard-coding
    business assumptions into the database adapter.
    """

    name: str
    positive_kind: OutcomeKind
    horizon_days: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Target name cannot be empty.")

        if self.horizon_days <= 0:
            raise ValueError("Target horizon must be positive.")
