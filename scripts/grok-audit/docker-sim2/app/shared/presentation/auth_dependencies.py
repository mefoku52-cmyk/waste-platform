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
