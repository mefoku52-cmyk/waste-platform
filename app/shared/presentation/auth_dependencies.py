from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.application.services import GetCurrentAuthContextService
from app.modules.auth.presentation.dependencies import get_auth_service
from app.modules.auth.presentation.schemas import CurrentUserResponse

bearer_scheme = HTTPBearer(auto_error=False)


async def require_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: GetCurrentAuthContextService = Depends(get_auth_service),
) -> CurrentUserResponse:
    if credentials is None:
        from app.shared.domain.exceptions import UnauthorizedDomainError
        raise UnauthorizedDomainError("Authentication required")
    return await service.execute(credentials.credentials)


def _user_email(current_user) -> str:
    u = getattr(current_user, "user", None)
    if u is not None:
        return (getattr(u, "email", None) or "").lower().strip()
    return (getattr(current_user, "email", None) or "").lower().strip()


def _role_codes(current_user) -> list[str]:
    codes = getattr(current_user, "roleCodes", None) or getattr(current_user, "role_codes", None) or []
    return [str(c).lower() for c in codes]


async def require_admin(current_user: CurrentUserResponse = Depends(require_current_user)) -> CurrentUserResponse:
    """Platform admin: email in PLATFORM_ADMIN_EMAILS or role code admin."""
    from app.core.config import settings
    from app.shared.domain.exceptions import ForbiddenDomainError

    email = _user_email(current_user)
    raw = getattr(settings, "platform_admin_emails", None)
    if raw is None:
        import os
        raw = os.getenv("PLATFORM_ADMIN_EMAILS", "admin@cmep-bootstrap.dev")
    admins = {e.strip().lower() for e in str(raw).split(",") if e.strip()}
    codes = _role_codes(current_user)
    if email in admins or "admin" in codes or "platform_admin" in codes:
        return current_user
    raise ForbiddenDomainError("Admin access required")
