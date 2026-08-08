"""admin infrastructure mappers."""

from app.modules.admin.domain.entities import AdminAuditEntryEntity
from app.modules.admin.domain.enums import AdminAuditEntryStatus
from app.modules.admin.infrastructure.models import AdminAuditEntryModel


def to_domain(model: AdminAuditEntryModel) -> AdminAuditEntryEntity:
    return AdminAuditEntryEntity(
        id=model.id,
        actor_user_id=model.actor_user_id,
        action=model.action,
        target_type=model.target_type,
        target_id=model.target_id,
        details=model.details,
        status=AdminAuditEntryStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by_user_id=model.created_by_user_id,
        updated_by_user_id=model.updated_by_user_id,
    )


def to_model(entity: AdminAuditEntryEntity) -> AdminAuditEntryModel:
    return AdminAuditEntryModel(
        id=entity.id,
        actor_user_id=entity.actor_user_id,
        action=entity.action,
        target_type=entity.target_type,
        target_id=entity.target_id,
        details=entity.details,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_user_id=entity.created_by_user_id,
        updated_by_user_id=entity.updated_by_user_id,
    )
