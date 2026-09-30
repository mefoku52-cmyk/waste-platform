"""Prediction API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictionAccessResponse(BaseModel):
    serviceEnabled: bool
    entitled: bool
    providerAvailable: bool
    status: str


class PredictionRequestSchema(BaseModel):
    subjectType: str = Field(..., min_length=1, max_length=64)
    subjectId: str = Field(..., min_length=1, max_length=128)
    context: dict[str, Any] = Field(default_factory=dict)


class PredictionResultResponse(BaseModel):
    status: str
    score: float | None = None
    confidence: str | None = None
    factors: list[str] = Field(default_factory=list)
    provider: str | None = None
    metadata: dict[str, Any] | None = None
