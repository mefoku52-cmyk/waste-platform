"""listings domain enums."""

from enum import Enum


class ListingsStatus(str, Enum):
    """Listings status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
