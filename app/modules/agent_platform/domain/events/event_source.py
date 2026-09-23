"""Event sources."""

from enum import Enum


class EventSource(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AI = "ai"
    TOOL = "tool"
    SERVICE = "service"
    SECURITY = "security"
    SYSTEM = "system"
