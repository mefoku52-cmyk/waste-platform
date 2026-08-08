"""inquiries domain enums."""

from enum import Enum


class InquiryStatus(str, Enum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"
