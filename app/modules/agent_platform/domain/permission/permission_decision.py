"""Permission decisions."""

from dataclasses import dataclass
from enum import Enum


class PermissionOutcome(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    outcome: PermissionOutcome
    reason: str
    policy_rule_id: str | None = None
