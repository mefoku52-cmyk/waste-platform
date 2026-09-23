"""Control-state persistence contract."""

from abc import ABC, abstractmethod

from ...domain.control.control_mode import ControlMode
from ...domain.control.emergency_state import EmergencyState


class ControlRepository(ABC):
    @abstractmethod
    async def get_mode(self) -> ControlMode:
        raise NotImplementedError

    @abstractmethod
    async def save_state(self, state: EmergencyState) -> EmergencyState:
        raise NotImplementedError

    @abstractmethod
    async def get_state(self) -> EmergencyState:
        raise NotImplementedError
