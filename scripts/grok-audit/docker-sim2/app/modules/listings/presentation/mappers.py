"""listings mappers."""

from ..domain.entities import ListingsEntity
from .schemas import ListingsResponse


def map_entity_to_response(entity: ListingsEntity) -> ListingsResponse:
    """Map entity to response."""
    return ListingsResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
