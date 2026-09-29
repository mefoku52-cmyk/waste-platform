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


_ACTION_TO_MODE = {
    "enable_ai": None,
    "disable_ai": "ai_disabled",
    "read_only": "read_only",
    "lockdown": "lockdown",
    "revoke_tools": "read_only",
    "revoke_admin": "lockdown",
    "freeze_operations": "lockdown",
    "release_lockdown": None,
}


class DefaultControlService(ControlService):
    """Konkretna implementacia ControlService."""

    def __init__(self, *, repository) -> None:
        self._repository = repository

    async def get_mode(self) -> ControlMode:
        return await self._repository.get_mode()

    async def apply(self, action: ControlAction, actor_id: str, reason: str) -> ControlMode:
        from datetime import UTC, datetime

        from app.modules.agent_platform.domain.control.emergency_state import (
            EmergencyState,
        )

        action_value = action.value if hasattr(action, "value") else str(action)
        target_mode_value = _ACTION_TO_MODE.get(action_value, "normal")
        target_mode = (
            ControlMode.NORMAL if target_mode_value is None else ControlMode(target_mode_value)
        )

        new_state = EmergencyState(
            mode=target_mode,
            changed_at=datetime.now(UTC),
            changed_by=actor_id,
            reason=reason,
        )
        await self._repository.save_state(new_state)
        return target_mode


_ACTION_TO_MODE = {
    "enable_ai": None,
    "disable_ai": "ai_disabled",
    "read_only": "read_only",
    "lockdown": "lockdown",
    "revoke_tools": "read_only",
    "revoke_admin": "lockdown",
    "freeze_operations": "lockdown",
    "release_lockdown": None,
}
