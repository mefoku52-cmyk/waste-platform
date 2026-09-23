from __future__ import annotations

from dataclasses import dataclass

from app.modules.prediction.application.baseline_pipeline_provider import (
    BaselinePipelineProvider,
)
from app.modules.prediction.domain.provider import PredictionProvider


@dataclass
class PredictionProviderRegistry:
    """
    Runtime registry for providers used by the feature/model pipeline.

    The stable public provider boundary remains domain.provider.
    """

    providers: dict[str, object]

    def __init__(
        self,
        providers: dict[str, object] | None = None,
    ) -> None:
        self.providers = dict(providers or {})

    def register(
        self,
        provider: object,
    ) -> None:
        name = getattr(provider, "name", None)

        if not isinstance(name, str) or not name:
            raise ValueError("Prediction provider must expose a non-empty name")

        self.providers[name] = provider

    def get(
        self,
        name: str,
    ) -> object | None:
        return self.providers.get(name)

    def require(
        self,
        name: str,
    ) -> object:
        provider = self.get(name)

        if provider is None:
            raise KeyError(f"Prediction provider not registered: {name}")

        return provider

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self.providers))

    def available(self) -> tuple[object, ...]:
        result: list[object] = []

        for provider in self.providers.values():
            availability = getattr(
                provider,
                "availability",
                None,
            )

            if availability is None:
                result.append(provider)
                continue

            value = getattr(
                availability,
                "value",
                availability,
            )

            if value not in {
                "disabled",
                "unavailable",
            }:
                result.append(provider)

        return tuple(result)


def create_default_provider_registry() -> PredictionProviderRegistry:
    registry = PredictionProviderRegistry()

    registry.register(BaselinePipelineProvider())

    return registry


__all__ = [
    "PredictionProvider",
    "PredictionProviderRegistry",
    "create_default_provider_registry",
]
