"""compliance infrastructure mappers."""

from app.modules.compliance.domain.entities import ComplianceRecordEntity
from app.modules.compliance.domain.enums import ComplianceRecordStatus
from app.modules.compliance.infrastructure.models import ComplianceRecordModel


def to_domain(model: ComplianceRecordModel) -> ComplianceRecordEntity:
    return ComplianceRecordEntity(
        id=model.id,
        company_id=model.company_id,
        regulation_type=model.regulation_type,
        document_ref=model.document_ref,
        valid_until=model.valid_until,
        notes=model.notes,
        status=ComplianceRecordStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: ComplianceRecordEntity) -> ComplianceRecordModel:
    return ComplianceRecordModel(
        id=entity.id,
        company_id=entity.company_id,
        regulation_type=entity.regulation_type,
        document_ref=entity.document_ref,
        valid_until=entity.valid_until,
        notes=entity.notes,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
