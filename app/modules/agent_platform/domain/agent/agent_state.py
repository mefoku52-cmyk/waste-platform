"""Agent runtime state."""

from enum import Enum


class AgentState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    READ_ONLY = "read_only"
    DISABLED = "disabled"
    EMERGENCY_STOP = "emergency_stop"
