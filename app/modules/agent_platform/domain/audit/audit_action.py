"""Audit actions."""

from enum import Enum


class AuditAction(str, Enum):
    READ = "read"
    SEARCH = "search"
    PREPARE = "prepare"
    REQUEST = "request"
    APPROVE = "approve"
    DENY = "deny"
    EXECUTE = "execute"
    BLOCK = "block"
    CONTROL_CHANGE = "control_change"
    SECURITY_EVENT = "security_event"
