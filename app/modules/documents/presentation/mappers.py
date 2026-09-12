"""documents mappers."""

from ..domain.entities import DocumentEntity
from .schemas import DocumentResponse


def map_entity_to_response(entity: DocumentEntity) -> DocumentResponse:
    """Map entity to response."""
    return DocumentResponse(
        data=entity,
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
