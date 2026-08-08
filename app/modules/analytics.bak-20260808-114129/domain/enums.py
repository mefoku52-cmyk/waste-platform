"""analytics domain enums."""

from enum import Enum


class AnalyticsStatus(str, Enum):
    """Analytics status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
