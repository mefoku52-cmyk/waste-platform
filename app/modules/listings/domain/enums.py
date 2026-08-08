"""listings domain enums."""

from enum import Enum


class ListingsStatus(str, Enum):
    """Listing workflow status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    RESERVED = "reserved"
    COMPLETED = "completed"
    ARCHIVED = "archived"
