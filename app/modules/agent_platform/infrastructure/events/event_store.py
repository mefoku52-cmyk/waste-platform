"""Event store contract."""

from abc import ABC, abstractmethod

from ...domain.events.platform_event import PlatformEvent


class EventStore(ABC):
    """Persistence/query boundary for platform events."""

    @abstractmethod
    async def append(self, event: PlatformEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, event_id: str) -> PlatformEvent | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_correlation(
        self,
        correlation_id: str,
    ) -> tuple[PlatformEvent, ...]:
        raise NotImplementedError


class SqlAlchemyEventStore(EventStore):
    """SQLAlchemy implementacia EventStore.

    Pouziva tabulku activity_events (rovnako ako SqlAlchemyEventPublisher).
    correlation_id je ulozene v payload JSON, rovnako ako source a target.
    """

    def __init__(self, session) -> None:
        self._session = session

    async def append(self, event: PlatformEvent) -> None:
        import json
        from datetime import UTC
        from uuid import UUID, uuid4

        from app.modules.events.infrastructure.models import ActivityEventModel

        payload_dict = {
            "source": event.source.value,
            "correlation_id": event.correlation_id,
            "target": event.target,
            **event.payload,
        }
        try:
            event_uuid = UUID(event.event_id)
        except (ValueError, TypeError):
            event_uuid = uuid4()

        created_at = event.occurred_at
        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(UTC).replace(tzinfo=None)

        row = ActivityEventModel(
            id=event_uuid,
            event_type=event.event_type.value,
            actor_user_id=event.actor_id,
            payload=json.dumps(payload_dict, ensure_ascii=False, default=str),
            created_at=created_at,
        )
        self._session.add(row)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def get(self, event_id: str) -> PlatformEvent | None:
        from uuid import UUID

        from sqlalchemy import select

        from app.modules.events.infrastructure.models import ActivityEventModel

        try:
            eid = UUID(event_id)
        except (ValueError, TypeError):
            return None

        row = (
            await self._session.execute(
                select(ActivityEventModel).where(ActivityEventModel.id == eid)
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_correlation(
        self,
        correlation_id: str,
    ) -> tuple[PlatformEvent, ...]:
        from sqlalchemy import select

        from app.modules.events.infrastructure.models import ActivityEventModel

        pattern = f'%"correlation_id": "{correlation_id}"%'
        rows = (
            (
                await self._session.execute(
                    select(ActivityEventModel)
                    .where(ActivityEventModel.payload.like(pattern))
                    .order_by(ActivityEventModel.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        return tuple(self._to_domain(r) for r in rows)

    @staticmethod
    def _to_domain(row) -> PlatformEvent:
        import json
        from datetime import UTC

        from app.modules.agent_platform.domain.events.event_source import EventSource
        from app.modules.agent_platform.domain.events.event_type import (
            PlatformEventType,
        )

        payload_dict: dict = {}
        if row.payload:
            try:
                payload_dict = json.loads(row.payload)
            except (TypeError, ValueError):
                payload_dict = {}

        source_value = payload_dict.pop("source", "system")
        correlation_id = payload_dict.pop("correlation_id", None)
        target = payload_dict.pop("target", None)

        occurred_at = row.created_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        try:
            event_id = str(row.id)
        except Exception:
            event_id = "unknown"

        try:
            etype = PlatformEventType(row.event_type)
        except ValueError:
            etype = PlatformEventType.AGENT_REQUESTED

        try:
            esource = EventSource(source_value)
        except ValueError:
            esource = EventSource.SYSTEM

        return PlatformEvent(
            event_id=event_id,
            event_type=etype,
            source=esource,
            occurred_at=occurred_at,
            actor_id=row.actor_user_id,
            correlation_id=correlation_id,
            target=target,
            payload=payload_dict,
        )
