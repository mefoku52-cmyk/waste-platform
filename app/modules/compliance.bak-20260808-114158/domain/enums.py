"""compliance domain enums."""

from enum import Enum


class ComplianceStatus(str, Enum):
    """Compliance status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
