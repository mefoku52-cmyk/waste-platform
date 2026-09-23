"""Security decisions."""

from enum import Enum


class SecurityDecision(str, Enum):
    ALLOW = "allow"
    MONITOR = "monitor"
    ALERT = "alert"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
