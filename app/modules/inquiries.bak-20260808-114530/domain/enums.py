"""inquiries domain enums."""

from enum import Enum


class InquiriesStatus(str, Enum):
    """Inquiries status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
