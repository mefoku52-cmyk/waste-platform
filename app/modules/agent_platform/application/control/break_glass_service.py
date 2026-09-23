"""Break-glass service contract."""

from abc import ABC, abstractmethod

from ...domain.control.break_glass import BreakGlassRequest


class BreakGlassService(ABC):
    @abstractmethod
    async def request(self, request: BreakGlassRequest) -> BreakGlassRequest:
        raise NotImplementedError
