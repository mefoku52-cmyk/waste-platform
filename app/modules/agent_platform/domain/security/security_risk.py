"""Security risk representation."""

from dataclasses import dataclass
from enum import Enum


class SecurityRiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SecurityRisk:
    level: SecurityRiskLevel
    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
