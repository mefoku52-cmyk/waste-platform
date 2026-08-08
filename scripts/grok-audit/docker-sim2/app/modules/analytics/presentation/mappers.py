"""analytics mappers."""

from ..domain.entities import AnalyticsEntity
from .schemas import AnalyticsResponse


def map_entity_to_response(entity: AnalyticsEntity) -> AnalyticsResponse:
    """Map entity to response."""
    return AnalyticsResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
