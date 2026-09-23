"""Event dispatcher contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventDispatcher(ABC):
    @abstractmethod
    async def dispatch(self, event: PlatformEvent) -> None:
        raise NotImplementedError
