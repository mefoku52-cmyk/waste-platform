from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    InvalidTransitionDomainError,
    NotFoundDomainError,
    UnauthorizedDomainError,
    ValidationDomainError,
)


def _request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")


def _error_payload(
    request: Request,
    *,
    error_code: str,
    message: str,
    details=None,
):
    return {
        "error_code": error_code,
        "message": message,
        "details": details,
        "request_id": _request_id(request),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundDomainError)
    async def not_found_handler(request: Request, exc: NotFoundDomainError):
        return JSONResponse(
            status_code=404,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(ConflictDomainError)
    async def conflict_handler(request: Request, exc: ConflictDomainError):
        return JSONResponse(
            status_code=409,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(ValidationDomainError)
    async def validation_handler(request: Request, exc: ValidationDomainError):
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(UnauthorizedDomainError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedDomainError):
        return JSONResponse(
            status_code=401,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(ForbiddenDomainError)
    async def forbidden_handler(request: Request, exc: ForbiddenDomainError):
        return JSONResponse(
            status_code=403,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
            ),
        )

    @app.exception_handler(InvalidTransitionDomainError)
    async def invalid_transition_handler(request: Request, exc: InvalidTransitionDomainError):
        return JSONResponse(
            status_code=409,
            content=_error_payload(
                request,
                error_code=exc.code,
                message=exc.message,
                details={
                    "current_status": exc.current_status,
                    "attempted_status": exc.attempted_status,
                    "allowed_transitions": exc.allowed_transitions,
                },
            ),
        )
