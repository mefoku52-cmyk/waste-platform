"""admin domain enums."""

from enum import Enum


class AdminStatus(str, Enum):
    """Admin status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
