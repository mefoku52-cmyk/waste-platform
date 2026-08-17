"""Unified API error payload."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ApiErrorBody(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable message")
    details: Optional[Any] = None
    request_id: Optional[str] = None
