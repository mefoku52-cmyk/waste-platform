"""documents domain enums."""

from enum import Enum


class DocumentsStatus(str, Enum):
    """Documents status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
