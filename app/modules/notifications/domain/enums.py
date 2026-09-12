"""notifications domain enums."""

from enum import Enum


class NotificationsStatus(str, Enum):
    """Notifications status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
