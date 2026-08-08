"""admin domain enums."""

from enum import Enum


class AdminAuditEntryStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
