from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.timezone import to_naive_utc

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


class SqlAlchemyControlRepository(ControlRepository):
    """SQLAlchemy implementation of control-state persistence.

    Pouziva jeden riadok v `agent_control_state` s id='current'.
    Ak riadok neexistuje, vrati normalny stav a nezapisuje.
    """

    _SINGLETON_ID = "current"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_mode(self) -> ControlMode:
        state = await self.get_state()
        return state.mode

    async def save_state(self, state: EmergencyState) -> EmergencyState:
        from app.modules.agent_platform.infrastructure.models import ControlStateModel

        m = await self._session.get(ControlStateModel, self._SINGLETON_ID)
        if m is None:
            m = ControlStateModel(
                id=self._SINGLETON_ID,
                mode=state.mode.value,
                changed_at=to_naive_utc(state.changed_at),
                changed_by=state.changed_by,
                reason=state.reason,
            )
            self._session.add(m)
        else:
            m.mode = state.mode.value
            m.changed_at = state.changed_at
            m.changed_by = state.changed_by
            m.reason = state.reason
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return state

    async def get_state(self) -> EmergencyState:
        from app.modules.agent_platform.infrastructure.models import ControlStateModel

        m = await self._session.get(ControlStateModel, self._SINGLETON_ID)
        if m is None:
            return EmergencyState.normal()
        return EmergencyState(
            mode=ControlMode(m.mode),
            changed_at=m.changed_at,
            changed_by=m.changed_by,
            reason=m.reason,
        )
