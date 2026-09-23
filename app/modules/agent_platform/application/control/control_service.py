"""Control service contract."""

from abc import ABC, abstractmethod

from ...domain.control.control_action import ControlAction
from ...domain.control.control_mode import ControlMode


class ControlService(ABC):
    @abstractmethod
    async def get_mode(self) -> ControlMode:
        raise NotImplementedError

    @abstractmethod
    async def apply(self, action: ControlAction, actor_id: str, reason: str) -> ControlMode:
        raise NotImplementedError
