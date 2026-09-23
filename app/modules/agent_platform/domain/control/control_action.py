"""Control actions."""

from enum import Enum


class ControlAction(str, Enum):
    ENABLE_AI = "enable_ai"
    DISABLE_AI = "disable_ai"
    READ_ONLY = "read_only"
    LOCKDOWN = "lockdown"
    REVOKE_TOOLS = "revoke_tools"
    REVOKE_ADMIN = "revoke_admin"
    FREEZE_OPERATIONS = "freeze_operations"
    RELEASE_LOCKDOWN = "release_lockdown"
