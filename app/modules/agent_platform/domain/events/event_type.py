"""Agent Platform event types."""

from enum import Enum


class PlatformEventType(str, Enum):
    AGENT_REQUESTED = "agent.requested"
    AGENT_RESPONDED = "agent.responded"

    TOOL_REQUESTED = "tool.requested"
    TOOL_ALLOWED = "tool.allowed"
    TOOL_DENIED = "tool.denied"
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"

    POLICY_EVALUATED = "policy.evaluated"
    PERMISSION_EVALUATED = "permission.evaluated"

    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_DENIED = "approval.denied"
    APPROVAL_EXPIRED = "approval.expired"

    SECURITY_OBSERVED = "security.observed"
    SECURITY_SIGNAL = "security.signal"
    SECURITY_ALERT = "security.alert"

    CONTROL_CHANGED = "control.changed"
    EMERGENCY_ACTIVATED = "emergency.activated"

    AUDIT_RECORDED = "audit.recorded"
