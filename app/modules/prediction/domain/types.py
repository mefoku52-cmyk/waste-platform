from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PredictionAvailability(str, Enum):
    """
    Runtime availability of the prediction provider.

    ACTIVE:
        Provider is enabled and available.

    DISABLED:
        Provider is intentionally disabled by platform configuration.

    UNAVAILABLE:
        Provider is configured/allowed in principle, but the actual
        provider cannot currently serve the request.
    """

    ACTIVE = "active"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class PredictionStatus(str, Enum):
    """
    Result status.

    Notice that UNAVAILABLE is deliberately different from a numeric
    prediction of zero. No prediction must never be represented as
    a negative or zero prediction merely because the service is off.
    """

    AVAILABLE = "available"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    NOT_ENTITLED = "not_entitled"


@dataclass(frozen=True)
class PredictionRequest:
    """
    Provider-neutral prediction request.

    The prediction module must not know about HTTP, FastAPI, JWT,
    frontend components, payment providers, or database sessions.
    Those concerns belong outside this boundary.
    """

    subject_type: str
    subject_id: str
    context: dict[str, Any]


@dataclass(frozen=True)
class PredictionResult:
    """
    Provider-neutral structured prediction result.

    score:
        Optional normalized prediction score in range 0..1.

    confidence:
        Optional confidence descriptor.

    factors:
        Structured reasons that can later be consumed by UI or AI.

    provider:
        Identifier of the provider which generated the result.
    """

    status: PredictionStatus
    score: float | None = None
    confidence: str | None = None
    factors: tuple[str, ...] = ()
    provider: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.score is not None and not 0.0 <= self.score <= 1.0:
            raise ValueError("Prediction score must be between 0 and 1.")
