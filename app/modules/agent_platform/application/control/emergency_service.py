from app.modules.agent_platform.domain.control.control_mode import ControlMode

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


class DefaultEmergencyService(EmergencyService):
    """Konkretna implementacia EmergencyService."""

    def __init__(self, *, repository) -> None:
        self._repository = repository

    async def activate(self, actor_id: str, reason: str) -> EmergencyState:
        from datetime import UTC, datetime

        state = EmergencyState(
            mode=ControlMode.EMERGENCY,
            changed_at=datetime.now(UTC),
            changed_by=actor_id,
            reason=reason,
        )
        await self._repository.save_state(state)
        return state

    async def release(self, actor_id: str, reason: str) -> EmergencyState:
        from datetime import UTC, datetime

        state = EmergencyState(
            mode=ControlMode.NORMAL,
            changed_at=datetime.now(UTC),
            changed_by=actor_id,
            reason=reason,
        )
        await self._repository.save_state(state)
        return state
