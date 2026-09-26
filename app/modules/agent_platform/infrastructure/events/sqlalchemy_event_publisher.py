"""SQLAlchemy event publisher – best-effort persistence to activity_events."""

from __future__ import annotations

import json
import uuid
from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.events.platform_event import PlatformEvent
from app.modules.agent_platform.infrastructure.events.event_publisher import (
    EventPublisher,
)


class SqlAlchemyEventPublisher(EventPublisher):
    """Best-effort publisher: writes a PlatformEvent to activity_events.

    source and correlation_id are stored inside the payload JSON since
    activity_events has no dedicated columns for them.
    Failure must never break the caller.
    """

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def publish(self, event: PlatformEvent) -> None:
        try:
            from app.modules.events.infrastructure.models import ActivityEventModel

            payload_dict = {
                "source": event.source.value,
                "correlation_id": event.correlation_id,
                "target": event.target,
                **event.payload,
            }
            try:
                event_uuid = uuid.UUID(event.event_id)
            except (ValueError, TypeError):
                event_uuid = uuid.uuid4()

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
            await self._session.flush()
        except Exception:
            # Best-effort: never break the caller.
            pass
