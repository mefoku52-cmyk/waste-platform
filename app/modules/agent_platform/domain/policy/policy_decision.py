"""Policy decisions."""

from dataclasses import dataclass
from enum import Enum


class PolicyOutcome(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    outcome: PolicyOutcome
    rule_id: str | None
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason is required")
