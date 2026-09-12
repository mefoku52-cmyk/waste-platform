from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.infrastructure.models import RefreshSessionModel


def to_entity(model: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=model.id,
        user_id=model.user_id,
        family_id=model.family_id,
        jti=model.jti,
        expires_at=model.expires_at if model.expires_at else None,
        revoked_at=model.revoked_at if model.revoked_at else None,
        reuse_detected_at=model.reuse_detected_at if model.reuse_detected_at else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
