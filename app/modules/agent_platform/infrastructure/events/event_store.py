"""Event store contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventStore(ABC):
    """Persistence/query boundary for platform events."""

    @abstractmethod
    async def append(self, event: PlatformEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, event_id: str) -> PlatformEvent | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_correlation(
        self,
        correlation_id: str,
    ) -> tuple[PlatformEvent, ...]:
        raise NotImplementedError
