from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    InvalidTransitionDomainError,
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

    @app.exception_handler(ForbiddenDomainError)
    async def forbidden_domain_handler(request: Request, exc: ForbiddenDomainError):
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc) or "Forbidden"},
        )

    @app.exception_handler(ConflictDomainError)
    async def conflict_domain_handler(request: Request, exc: ConflictDomainError):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc) or "Conflict"},
        )

    @app.exception_handler(InvalidTransitionDomainError)
    async def invalid_transition_domain_handler(
        request: Request, exc: InvalidTransitionDomainError
    ):
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc) or "Invalid status transition",
                "currentStatus": exc.current_status,
                "attemptedStatus": exc.attempted_status,
                "allowedTransitions": exc.allowed_transitions,
            },
        )
