"""documents mappers."""

from ..domain.entities import DocumentsEntity
from .schemas import DocumentsResponse


def map_entity_to_response(entity: DocumentsEntity) -> DocumentsResponse:
    """Map entity to response."""
    return DocumentsResponse(
        id=str(entity.id),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
