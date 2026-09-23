from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineConfig:
    """
    Configuration for the deterministic baseline.

    This is deliberately transparent and versioned.

    The baseline is NOT presented as learned intelligence.
    It exists to establish a measurable reference point.
    """

    version: str = "baseline-1"

    # Historical activity signals.
    views_weight: float = 0.20
    inquiries_weight: float = 0.35
    recommendations_weight: float = 0.10
    events_weight: float = 0.10

    # Matching signals.
    material_match_weight: float = 0.15
    location_match_weight: float = 0.10

    # Distance decay.
    distance_scale_km: float = 100.0

    # Minimum evidence required to call the result available.
    minimum_evidence: int = 1

    def total_weight(self) -> float:
        return (
            self.views_weight
            + self.inquiries_weight
            + self.recommendations_weight
            + self.events_weight
            + self.material_match_weight
            + self.location_match_weight
        )

    def validate(self) -> None:
        weights = (
            self.views_weight,
            self.inquiries_weight,
            self.recommendations_weight,
            self.events_weight,
            self.material_match_weight,
            self.location_match_weight,
        )

        if any(weight < 0 for weight in weights):
            raise ValueError("Baseline weights cannot be negative.")

        if self.total_weight() <= 0:
            raise ValueError("Baseline requires at least one positive weight.")

        if self.distance_scale_km <= 0:
            raise ValueError("distance_scale_km must be positive.")

        if self.minimum_evidence < 0:
            raise ValueError("minimum_evidence cannot be negative.")
