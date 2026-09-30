from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.infrastructure.models import RefreshSessionModel


def to_entity(model: RefreshSessionModel) -> RefreshSession:
    family = getattr(model, "token_family_id", None) or getattr(model, "family_id", None)
    jti = getattr(model, "refresh_token_jti", None) or getattr(model, "jti", None)
    return RefreshSession(
        id=model.id,
        user_id=model.user_id,
        family_id=family,
        jti=jti,
        expires_at=model.expires_at or None,
        revoked_at=model.revoked_at or None,
        reuse_detected_at=model.reuse_detected_at or None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
