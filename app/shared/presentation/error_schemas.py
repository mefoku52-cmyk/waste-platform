"""Unified API error response schemas and OpenAPI response helpers."""

from typing import Any

from pydantic import BaseModel, Field


class ApiErrorResponse(BaseModel):
    error_code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | list[Any] | str | None = Field(
        default=None,
        description="Optional structured details for debugging or validation",
    )
    request_id: str | None = Field(
        default=None,
        description="Request correlation identifier for tracing",
    )


class FieldError(BaseModel):
    field: str = Field(..., description="Invalid field name")
    message: str = Field(..., description="Validation error message")


class ValidationApiErrorResponse(ApiErrorResponse):
    details: dict[str, Any] | list[Any] | str | None = Field(default=None)
    field_errors: list[FieldError] = Field(default_factory=list)


class InvalidTransitionDetails(BaseModel):
    current_status: str
    attempted_status: str
    allowed_transitions: list[str]


class InvalidTransitionApiErrorResponse(ApiErrorResponse):
    details: InvalidTransitionDetails | dict[str, Any] | None = None


def error_responses(*status_codes: int):
    mapping = {
        400: {"model": ApiErrorResponse, "description": "Bad Request"},
        401: {"model": ApiErrorResponse, "description": "Unauthorized"},
        403: {"model": ApiErrorResponse, "description": "Forbidden"},
        404: {"model": ApiErrorResponse, "description": "Not Found"},
        409: {"model": InvalidTransitionApiErrorResponse, "description": "Conflict"},
        422: {"model": ValidationApiErrorResponse, "description": "Validation Error"},
        500: {"model": ApiErrorResponse, "description": "Internal Server Error"},
    }
    return {code: mapping[code] for code in status_codes if code in mapping}
