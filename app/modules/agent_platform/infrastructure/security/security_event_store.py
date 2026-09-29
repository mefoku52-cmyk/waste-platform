from sqlalchemy.ext.asyncio import AsyncSession

"""Security event storage contract."""

from abc import ABC, abstractmethod

from ...domain.security.security_observation import SecurityObservation
from ...domain.security.security_signal import SecuritySignal


class SecurityEventStore(ABC):
    """Storage boundary for security observations/signals."""

    @abstractmethod
    async def store_observation(
        self,
        observation: SecurityObservation,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def store_signal(
        self,
        signal: SecuritySignal,
    ) -> None:
        raise NotImplementedError


class SqlAlchemySecurityEventStore(SecurityEventStore):
    """SQLAlchemy implementation of security event storage.

    Observation aj signal zdielaju jednu tabulku (agent_security_events),
    rozlisene stlpcom `kind`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store_observation(self, observation: SecurityObservation) -> None:
        import json

        from app.modules.agent_platform.infrastructure.models import SecurityEventModel

        m = SecurityEventModel(
            event_id=observation.observation_id,
            kind="observation",
            pattern=observation.pattern.value,
            source=observation.source,
            actor_id=observation.actor_id,
            target=observation.target,
            evidence=json.dumps(observation.evidence, default=str)
            if observation.evidence
            else None,
            confidence=None,
            source_observation_id=None,
            occurred_at=observation.observed_at,
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def store_signal(self, signal: SecuritySignal) -> None:
        from app.modules.agent_platform.infrastructure.models import SecurityEventModel

        m = SecurityEventModel(
            event_id=signal.signal_id,
            kind="signal",
            pattern=signal.pattern.value,
            source=None,
            actor_id=None,
            target=None,
            evidence=None,
            confidence=float(signal.confidence),
            source_observation_id=signal.source_observation_id,
            occurred_at=signal.created_at,
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
