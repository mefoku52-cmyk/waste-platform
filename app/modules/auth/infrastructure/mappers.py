from uuid import UUID

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.infrastructure.models import RefreshSessionModel


def to_domain(model: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=UUID(model.id),
        user_id=UUID(model.user_id),
        token_family_id=model.token_family_id,
        refresh_token_jti=model.refresh_token_jti,
        refresh_token_hash=model.refresh_token_hash,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        replaced_by_jti=model.replaced_by_jti,
        reuse_detected_at=model.reuse_detected_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: RefreshSession) -> RefreshSessionModel:
    return RefreshSessionModel(
        id=str(entity.id),
        user_id=str(entity.user_id),
        token_family_id=entity.token_family_id,
        refresh_token_jti=entity.refresh_token_jti,
        refresh_token_hash=entity.refresh_token_hash,
        expires_at=entity.expires_at,
        revoked_at=entity.revoked_at,
        replaced_by_jti=entity.replaced_by_jti,
        reuse_detected_at=entity.reuse_detected_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )
