"""Event bus contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: PlatformEvent) -> None:
        raise NotImplementedError
