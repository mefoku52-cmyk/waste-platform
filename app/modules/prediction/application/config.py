from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


@dataclass(frozen=True)
class PredictionConfig:
    """
    Technical runtime configuration.

    This is deliberately separate from user entitlement.

    PREDICTION_SERVICE_ENABLED controls whether the platform exposes
    the prediction provider at runtime.

    It does NOT grant a user access.
    """

    service_enabled: bool = False

    @classmethod
    def from_environment(cls) -> PredictionConfig:
        return cls(
            service_enabled=_env_bool(
                "PREDICTION_SERVICE_ENABLED",
                default=False,
            )
        )
