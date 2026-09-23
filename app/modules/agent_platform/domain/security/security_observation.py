"""Security observations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .security_pattern import SecurityPattern


@dataclass(frozen=True, slots=True)
class SecurityObservation:
    """Raw observation used by the security layer.

    An observation is evidence, not a final accusation or authorization
    decision.
    """

    observation_id: str
    pattern: SecurityPattern
    source: str
    actor_id: str | None
    target: str | None
    evidence: dict[str, Any]
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id is required")
        if not self.source.strip():
            raise ValueError("source is required")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
