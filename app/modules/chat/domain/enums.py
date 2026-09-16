"""chat domain enums."""

from enum import Enum


class ChatThreadStatus(str, Enum):
    OPEN = "open"
    ARCHIVED = "archived"
    CLOSED = "closed"
