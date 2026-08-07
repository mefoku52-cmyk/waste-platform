"""Clock port interface."""

from datetime import datetime, timezone
from abc import ABC, abstractmethod


class Clock(ABC):
    """Abstract clock interface."""
    
    @abstractmethod
    def now(self) -> datetime:
        """Return current UTC datetime."""
        pass


class SystemClock(Clock):
    """Real system clock."""
    
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
