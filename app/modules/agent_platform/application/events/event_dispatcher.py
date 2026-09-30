"""Event dispatcher contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventDispatcher(ABC):
    @abstractmethod
    async def dispatch(self, event: PlatformEvent) -> None:
        raise NotImplementedError


class DefaultEventDispatcher(EventDispatcher):
    """Konkretna implementacia EventDispatcher.

    Drzi registry: typ eventu -> zoznam handlerov. Volanie dispatch
    prejde vsetky handlery pre dany typ. Chyba v jednom handleri
    nezastavi ostatne.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def register(self, event_type: str, handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def dispatch(self, event: PlatformEvent) -> None:
        event_type_value = (
            event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        )
        for handler in self._handlers.get(event_type_value, []):
            try:
                await handler(event)
            except Exception:
                continue
