"""admin mappers."""

from ..domain.entities import AdminEntity
from .schemas import AdminResponse


def map_entity_to_response(entity: AdminEntity) -> AdminResponse:
    """Map entity to response."""
    return AdminResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
