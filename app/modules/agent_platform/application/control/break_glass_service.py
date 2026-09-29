"""Break-glass service contract."""

from abc import ABC, abstractmethod

from ...domain.control.break_glass import BreakGlassRequest


class BreakGlassService(ABC):
    @abstractmethod
    async def request(self, request: BreakGlassRequest) -> BreakGlassRequest:
        raise NotImplementedError


class DefaultBreakGlassService(BreakGlassService):
    """Konkretna implementacia BreakGlassService."""

    def __init__(self, *, repository=None) -> None:
        self._repository = repository

    async def request(self, request: BreakGlassRequest) -> BreakGlassRequest:
        return request
