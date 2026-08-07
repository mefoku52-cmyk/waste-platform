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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundDomainError)
    async def not_found_handler(request: Request, exc: NotFoundDomainError):
        return JSONResponse(status_code=404, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ConflictDomainError)
    async def conflict_handler(request: Request, exc: ConflictDomainError):
        return JSONResponse(status_code=409, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ValidationDomainError)
    async def validation_handler(request: Request, exc: ValidationDomainError):
        return JSONResponse(status_code=422, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(UnauthorizedDomainError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedDomainError):
        return JSONResponse(status_code=401, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ForbiddenDomainError)
    async def forbidden_handler(request: Request, exc: ForbiddenDomainError):
        return JSONResponse(status_code=403, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(InvalidTransitionDomainError)
    async def invalid_transition_handler(request: Request, exc: InvalidTransitionDomainError):
        return JSONResponse(
            status_code=400,
            content={
                "code": exc.code,
                "message": exc.message,
                "currentStatus": exc.current_status,
                "attemptedStatus": exc.attempted_status,
                "allowedTransitions": exc.allowed_transitions,
            },
        )
