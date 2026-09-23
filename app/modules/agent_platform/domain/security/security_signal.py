"""Security signal."""

from dataclasses import dataclass
from datetime import datetime

from .security_pattern import SecurityPattern


@dataclass(frozen=True, slots=True)
class SecuritySignal:
    """Normalized security signal.

    Confidence is a signal strength, not proof of malicious intent.
    """

    signal_id: str
    pattern: SecurityPattern
    confidence: float
    source_observation_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
