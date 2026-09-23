from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PredictionKind(StrEnum):
    """
    Explicit prediction target.

    We start with a generic probability target rather than pretending
    that the system already knows the final business outcome.
    """

    INTEREST = "interest"


class PredictionConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PredictionFactor:
    """
    Structured explanation factor.

    This is data, not an LLM-generated explanation.
    """

    name: str
    value: Any
    contribution: float | None = None
    source: str | None = None


@dataclass(frozen=True)
class PredictionResult:
    """
    Immutable result returned by a prediction provider.

    probability:
        Optional probability in [0, 1].

    confidence:
        Confidence classification.

    factors:
        Structured factors used by the predictor.

    provider:
        Stable provider name.

    model_version:
        Version of the predictor implementation/model.

    available:
        False means the provider could not produce a prediction.
        This MUST NOT be represented as probability=0.
    """

    kind: PredictionKind
    subject_type: str
    subject_id: str
    probability: float | None
    confidence: PredictionConfidence
    provider: str
    model_version: str
    available: bool
    factors: tuple[PredictionFactor, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.probability is not None:
            if not 0.0 <= self.probability <= 1.0:
                raise ValueError("Prediction probability must be in [0, 1].")

        if not self.available and self.probability is not None:
            raise ValueError("Unavailable prediction cannot contain a probability.")

        if self.available and self.probability is None:
            raise ValueError("Available prediction must contain a probability.")

    @property
    def percentage(self) -> float | None:
        if self.probability is None:
            return None

        return self.probability * 100.0
