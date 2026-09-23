"""Control modes for the Agent Platform."""

from enum import Enum


class ControlMode(str, Enum):
    NORMAL = "normal"
    READ_ONLY = "read_only"
    AI_DISABLED = "ai_disabled"
    LOCKDOWN = "lockdown"
    EMERGENCY = "emergency"
