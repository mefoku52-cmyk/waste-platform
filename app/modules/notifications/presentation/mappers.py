"""notifications mappers."""

from ..domain.entities import NotificationEntity
from .schemas import NotificationResponse


def map_entity_to_response(entity: NotificationEntity) -> NotificationResponse:
    """Map entity to response."""
    return NotificationResponse(
        data=entity,
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
