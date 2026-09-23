"""Event publisher contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventPublisher(ABC):
    """Infrastructure boundary for publishing Agent Platform events."""

    @abstractmethod
    async def publish(self, event: PlatformEvent) -> None:
        raise NotImplementedError
