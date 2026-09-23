from __future__ import annotations

from typing import Any

from app.modules.prediction.application.features import FeatureEngine
from app.modules.prediction.application.providers import (
    PredictionProviderRegistry,
)
from app.modules.prediction.domain.model import (
    PredictionKind,
    PredictionResult,
)


class PredictionPipeline:
    """
    Feature-to-baseline pipeline.

    This pipeline deliberately remains separate from the stable
    domain PredictionProvider boundary. It passes an already extracted
    FeatureSet directly to the baseline model implementation.
    """

    def __init__(
        self,
        *,
        feature_engine: FeatureEngine,
        providers: PredictionProviderRegistry,
        provider_name: str = "baseline",
    ) -> None:
        self._feature_engine = feature_engine
        self._providers = providers
        self._provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def predict(
        self,
        *,
        subject_type: str,
        subject_id: str,
        context: dict[str, Any] | None = None,
        kind: PredictionKind = PredictionKind.INTEREST,
    ) -> PredictionResult:
        features = await self._feature_engine.extract(
            subject_type=subject_type,
            subject_id=subject_id,
            context=context or {},
        )

        provider = self._providers.get(self._provider_name)

        if provider is None:
            from app.modules.prediction.application.disabled_provider import (
                DisabledPredictionProvider,
            )

            return await DisabledPredictionProvider(
                reason="provider_unavailable",
            ).predict(
                subject_type=subject_type,
                subject_id=subject_id,
                features=features,
                context=context,
                kind=kind,
            )

        predict = getattr(provider, "predict", None)

        if predict is None:
            from app.modules.prediction.application.disabled_provider import (
                DisabledPredictionProvider,
            )

            return await DisabledPredictionProvider(
                reason="provider_invalid",
            ).predict(
                subject_type=subject_type,
                subject_id=subject_id,
                features=features,
                context=context,
                kind=kind,
            )

        return await predict(
            subject_type=subject_type,
            subject_id=subject_id,
            features=features,
            context=context,
            kind=kind,
        )
