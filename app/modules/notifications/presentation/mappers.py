from ..domain.entities import NotificationEntity
from .schemas import NotificationData, NotificationResponse


def map_entity_to_response(entity: NotificationEntity) -> NotificationResponse:
    return NotificationResponse(
        data=NotificationData(
            id=entity.id,
            userId=entity.user_id,
            type=entity.type,
            title=entity.title,
            message=entity.message,
            isRead=entity.is_read,
            relatedEntityId=entity.related_entity_id,
            createdAt=entity.created_at,
            updatedAt=entity.updated_at,
        )
    )
