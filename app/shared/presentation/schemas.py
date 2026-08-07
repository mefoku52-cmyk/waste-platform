from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlationId: str | None = None
    details: dict[str, Any] | None = None


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    fieldErrors: list[FieldError] = []


class InvalidTransitionErrorResponse(ErrorResponse):
    currentStatus: str
    attemptedStatus: str
    allowedTransitions: list[str]
