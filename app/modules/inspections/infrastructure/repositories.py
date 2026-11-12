"""inspections repository implementation."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspections.domain.entities import InspectionEntity
from app.modules.inspections.domain.enums import InspectionEventType, InspectionState
from app.modules.inspections.infrastructure.mappers import (
    apply_event_to_entity,
    inspection_to_domain,
    inspection_to_model,
)
from app.modules.inspections.infrastructure.models import (
    InspectionEventModel,
    InspectionModel,
)


def _uid(x):
    if x is None:
        return None
    return x if isinstance(x, uuid.UUID) else uuid.UUID(str(x))


_ACTIVE_STATES = [s.value for s in InspectionState.active_states()]


class InspectionRepositoryImpl:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: InspectionEntity) -> InspectionEntity:
        m = inspection_to_model(entity)
        self.session.add(m)
        await self.session.commit()
        await self.session.refresh(m)
        return inspection_to_domain(m)

    async def get(self, inspection_id) -> InspectionEntity | None:
        r = await self.session.execute(
            select(InspectionModel).where(InspectionModel.id == _uid(inspection_id))
        )
        m = r.scalar_one_or_none()
        return inspection_to_domain(m) if m else None

    async def update(self, entity: InspectionEntity) -> InspectionEntity:
        m = await self.session.get(InspectionModel, _uid(entity.id))
        if m is None:
            raise ValueError("Inspection not found")
        m.room_id = entity.room_id
        m.viewer_user_id = entity.viewer_user_id
        m.viewer_company_id = entity.viewer_company_id
        m.viewer_thread_id = entity.viewer_thread_id
        m.state = entity.state.value
        m.consent_to_record = bool(entity.consent_to_record)
        m.recording_consent_at = entity.recording_consent_at
        m.ended_at = entity.ended_at
        m.updated_at = entity.updated_at
        m.updated_by_user_id = entity.updated_by_user_id
        await self.session.commit()
        await self.session.refresh(m)
        return inspection_to_domain(m)

    async def find_active_by_listing(self, listing_id) -> InspectionEntity | None:
        r = await self.session.execute(
            select(InspectionModel)
            .where(InspectionModel.listing_id == _uid(listing_id))
            .where(InspectionModel.state.in_(_ACTIVE_STATES))
            .order_by(InspectionModel.created_at.desc())
            .limit(1)
        )
        m = r.scalar_one_or_none()
        return inspection_to_domain(m) if m else None

    async def list_by_listing(self, listing_id, limit: int = 20) -> list[InspectionEntity]:
        r = await self.session.execute(
            select(InspectionModel)
            .where(InspectionModel.listing_id == _uid(listing_id))
            .order_by(InspectionModel.created_at.desc())
            .limit(limit)
        )
        return [inspection_to_domain(m) for m in r.scalars().all()]


class InspectionEventRepositoryImpl:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        event_uid: str,
        inspection_id,
        event_type: str,
        actor_user_id=None,
        room_id: str | None,
        role: str | None,
        reason: str | None,
        payload: str | None,
    ) -> bool:
        """Zapise event. Vrati False pri duplikate (idempotencia podla event_uid)."""
        dup = await self.session.execute(
            select(InspectionEventModel.id).where(InspectionEventModel.event_uid == event_uid)
        )
        if dup.scalar_one_or_none() is not None:
            return False
        row = InspectionEventModel(
            event_uid=str(event_uid)[:64],
            inspection_id=_uid(inspection_id),
            event_type=event_type,
            actor_user_id=_uid(actor_user_id),
            room_id=room_id,
            role=role,
            reason=reason,
            payload=payload,
        )
        self.session.add(row)
        await self.session.commit()
        return True

    @staticmethod
    def is_allowed_event_type(event_type: str) -> bool:
        try:
            return event_type in {e.value for e in InspectionEventType}
        except (ValueError, TypeError):
            return False
