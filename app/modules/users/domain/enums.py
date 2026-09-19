from enum import StrEnum


class UserStatus(StrEnum):
    INVITED = "invited"
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
