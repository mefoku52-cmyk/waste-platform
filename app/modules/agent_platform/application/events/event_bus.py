"""Event bus contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: PlatformEvent) -> None:
        raise NotImplementedError


class DefaultEventBus(EventBus):
    """Konkretna implementacia EventBus.

    Deleguje na publisher (napr. SqlAlchemyEventPublisher).
    Ak publisher nie je dany, je to no-op.
    """

    def __init__(self, *, publisher=None) -> None:
        self._publisher = publisher

    async def publish(self, event: PlatformEvent) -> None:
        if self._publisher is None:
            return
        await self._publisher.publish(event)
