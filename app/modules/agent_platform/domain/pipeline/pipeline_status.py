"""Agent pipeline status."""

from enum import StrEnum


class PipelineStatus(StrEnum):
    PROPOSED = "proposed"
    ALLOWED = "allowed"
    DENIED = "denied"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTED = "executed"
    FAILED = "failed"
