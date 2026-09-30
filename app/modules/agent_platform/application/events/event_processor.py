"""Event processor contract."""

import contextlib
from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventProcessor(ABC):
    @abstractmethod
    async def process(self, event: PlatformEvent) -> None:
        raise NotImplementedError


class DefaultEventProcessor(EventProcessor):
    """Konkretna implementacia EventProcessor.

    Spracuje event: zapise do audit service (ak je dany).
    Chyba v jednom kroku nezastavi dalsie.
    """

    def __init__(self, *, audit_service=None) -> None:
        self._audit_service = audit_service

    async def process(self, event: PlatformEvent) -> None:
        if self._audit_service is None:
            return
        with contextlib.suppress(Exception):
            await self._audit_service.record(event)
