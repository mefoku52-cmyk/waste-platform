"""notifications infrastructure mappers."""

from app.modules.notifications.domain.entities import NotificationEntity
from app.modules.notifications.infrastructure.models import NotificationModel


def to_domain(model: NotificationModel) -> NotificationEntity:
    return NotificationEntity(
        id=model.id,
        user_id=model.user_id,
        type=model.type,
        title=model.title,
        message=model.message,
        is_read=model.is_read,
        related_entity_id=model.related_entity_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: NotificationEntity) -> NotificationModel:
    return NotificationModel(
        id=entity.id,
        user_id=entity.user_id,
        type=entity.type,
        title=entity.title,
        message=entity.message,
        is_read=entity.is_read,
        related_entity_id=entity.related_entity_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
