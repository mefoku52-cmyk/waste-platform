"""notifications mappers."""

from ..domain.entities import NotificationsEntity
from .schemas import NotificationsResponse


def map_entity_to_response(entity: NotificationsEntity) -> NotificationsResponse:
    """Map entity to response."""
    return NotificationsResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
