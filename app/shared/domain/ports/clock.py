"""Clock port interface."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime


class Clock(ABC):
    """Abstract clock interface."""

    @abstractmethod
    def now(self) -> datetime:
        """Return current UTC datetime."""


class SystemClock(Clock):
    """Real system clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)
