"""documents infrastructure mappers."""

from app.modules.documents.domain.entities import DocumentEntity
from app.modules.documents.domain.enums import DocumentStatus
from app.modules.documents.infrastructure.models import DocumentModel


def to_domain(model: DocumentModel) -> DocumentEntity:
    return DocumentEntity(
        id=model.id,
        title=model.title,
        document_type=model.document_type,
        file_url=model.file_url,
        company_id=model.company_id,
        listing_id=model.listing_id,
        status=DocumentStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: DocumentEntity) -> DocumentModel:
    return DocumentModel(
        id=entity.id,
        title=entity.title,
        document_type=entity.document_type,
        file_url=entity.file_url,
        company_id=entity.company_id,
        listing_id=entity.listing_id,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
