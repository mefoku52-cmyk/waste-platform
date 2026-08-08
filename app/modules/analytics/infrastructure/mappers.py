"""analytics infrastructure mappers."""

from app.modules.analytics.domain.entities import AnalyticsEventEntity
from app.modules.analytics.infrastructure.models import AnalyticsEventModel


def to_domain(model: AnalyticsEventModel) -> AnalyticsEventEntity:
    return AnalyticsEventEntity(
        id=model.id,
        event_type=model.event_type,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        company_id=model.company_id,
        event_metadata=model.event_metadata,
        recorded_at=model.recorded_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: AnalyticsEventEntity) -> AnalyticsEventModel:
    return AnalyticsEventModel(
        id=entity.id,
        event_type=entity.event_type,
        entity_type=entity.entity_type,
        entity_id=entity.entity_id,
        company_id=entity.company_id,
        event_metadata=entity.event_metadata,
        recorded_at=entity.recorded_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
