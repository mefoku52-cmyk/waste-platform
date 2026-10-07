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


async def require_admin(
    current_user: CurrentUserResponse = Depends(require_current_user),
) -> CurrentUserResponse:
    """Platform admin: email in PLATFORM_ADMIN_EMAILS alebo rola `platform_admin`.

    Deleguje na `app.shared.presentation.authorization`, aby existovala jedina
    definicia platform-admin opravnenia. Tenant rola `admin` (z firemneho
    clenstva) tu ZAMERNE NEPOSTACUJE — spravca firmy nie je operator platformy.
    """
    from app.shared.presentation.authorization import require_platform_admin

    return require_platform_admin(current_user)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: GetCurrentAuthContextService = Depends(get_auth_service),
) -> CurrentUserResponse | None:
    """Ako require_current_user, ale vráti None ak nie je Authorization header.

    Používa sa pri endpointoch, ktoré môžu byť prístupné aj bez auth,
    napr. `<img src>` so signed URL (browser nevie poslať Bearer token).
    """
    if credentials is None:
        return None
    return await service.execute(credentials.credentials)
