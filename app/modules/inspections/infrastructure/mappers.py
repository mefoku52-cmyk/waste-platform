"""inspections mappers."""

from datetime import datetime
from uuid import UUID

from app.modules.inspections.domain.entities import InspectionEntity
from app.modules.inspections.domain.enums import InspectionState
from app.modules.inspections.infrastructure.models import InspectionModel


def _uuid_or_none(value):
    if value in (None, ""):
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


def inspection_to_domain(m: InspectionModel) -> InspectionEntity:
    return InspectionEntity(
        id=m.id,
        listing_id=m.listing_id,
        room_id=m.room_id,
        owner_user_id=m.owner_user_id,
        owner_company_id=m.owner_company_id,
        viewer_user_id=m.viewer_user_id,
        viewer_company_id=m.viewer_company_id,
        viewer_thread_id=m.viewer_thread_id,
        state=InspectionState(m.state) if m.state else InspectionState.CREATED,
        consent_to_record=bool(m.consent_to_record),
        recording_consent_at=m.recording_consent_at,
        ended_at=m.ended_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        created_by_user_id=m.created_by_user_id,
        updated_by_user_id=m.updated_by_user_id,
    )


def inspection_to_model(e: InspectionEntity) -> InspectionModel:
    return InspectionModel(
        id=e.id,
        listing_id=e.listing_id,
        room_id=e.room_id,
        owner_user_id=e.owner_user_id,
        owner_company_id=e.owner_company_id,
        viewer_user_id=e.viewer_user_id,
        viewer_company_id=e.viewer_company_id,
        viewer_thread_id=e.viewer_thread_id,
        state=e.state.value,
        consent_to_record=bool(e.consent_to_record),
        recording_consent_at=e.recording_consent_at,
        ended_at=e.ended_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
        created_by_user_id=e.created_by_user_id,
        updated_by_user_id=e.updated_by_user_id,
    )


def apply_event_to_entity(entity: InspectionEntity, *, event_type: str, role, room_id) -> None:
    """Stavovy stroj platformy podla eventov zo streamingu.

    Idempotentne: opakovany event v rovnakom stave nemeni nic spatne
    (napr. live -> live zostava live).
    """
    now = datetime.now()
    if event_type == "inspection_requested":
        if role == "owner":
            if room_id:
                entity.room_id = room_id
            if entity.state == InspectionState.CREATED:
                entity.state = InspectionState.ROOM_CREATED
            entity.updated_at = now
        elif role == "viewer" and entity.state.is_active:
            entity.state = InspectionState.REQUESTED
            entity.updated_at = now
    elif event_type == "inspection_accepted":
        if entity.state.is_active:
            entity.state = InspectionState.ACCEPTED
            entity.updated_at = now
    elif event_type == "inspection_started":
        if entity.state.is_active:
            entity.state = InspectionState.LIVE
            entity.updated_at = now
    elif event_type == "inspection_ended":
        entity.state = InspectionState.ENDED
        entity.ended_at = now
        entity.updated_at = now
