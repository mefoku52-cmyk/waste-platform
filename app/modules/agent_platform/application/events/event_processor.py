"""Event processor contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventProcessor(ABC):
    @abstractmethod
    async def process(self, event: PlatformEvent) -> None:
        raise NotImplementedError
