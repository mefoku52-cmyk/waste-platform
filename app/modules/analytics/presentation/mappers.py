"""analytics mappers."""

from ..domain.entities import AnalyticsEventEntity
from .schemas import AnalyticsEventResponse


def map_entity_to_response(entity: AnalyticsEventEntity) -> AnalyticsEventResponse:
    """Map entity to response."""
    return AnalyticsEventResponse(
        data=entity,
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
