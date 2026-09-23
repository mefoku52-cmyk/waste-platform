from __future__ import annotations

from app.modules.prediction.application.null_provider import (
    DisabledPredictionProvider,
)
from app.modules.prediction.application.providers import (
    PredictionProviderRegistry,
)


def test_registry_uses_domain_provider_contract() -> None:
    provider = DisabledPredictionProvider()

    registry = PredictionProviderRegistry()
    registry.register(provider)

    assert registry.get(provider.name) is provider
    assert provider.name in registry.names()
    assert registry.require(provider.name) is provider
