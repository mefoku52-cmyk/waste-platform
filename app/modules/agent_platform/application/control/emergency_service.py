"""Emergency control contract."""

from abc import ABC, abstractmethod

from ...domain.control.emergency_state import EmergencyState


class EmergencyService(ABC):
    @abstractmethod
    async def activate(self, actor_id: str, reason: str) -> EmergencyState:
        raise NotImplementedError

    @abstractmethod
    async def release(self, actor_id: str, reason: str) -> EmergencyState:
        raise NotImplementedError
