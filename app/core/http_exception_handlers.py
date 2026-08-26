from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.domain.exceptions import (
    NotFoundDomainError,
    UnauthorizedDomainError,
    ValidationDomainError,
)


def register_http_exception_handlers(app):
    @app.exception_handler(UnauthorizedDomainError)
    async def unauthorized_domain_handler(request: Request, exc: UnauthorizedDomainError):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc) or "Unauthorized"},
        )

    @app.exception_handler(NotFoundDomainError)
    async def not_found_domain_handler(request: Request, exc: NotFoundDomainError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc) or "Not found"},
        )

    @app.exception_handler(ValidationDomainError)
    async def validation_domain_handler(request: Request, exc: ValidationDomainError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc) or "Validation error"},
        )
