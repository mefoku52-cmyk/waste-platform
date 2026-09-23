from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.modules.prediction.application.recommendation_composer import (
    RecommendationScoreComposer,
)
from app.modules.prediction.domain.provider import PredictionProvider
from app.modules.prediction.domain.recommendation_score import (
    CombinedRecommendationScore,
)
from app.modules.prediction.domain.types import (
    PredictionRequest,
)


class BaseRecommendationScorer(Protocol):
    def __call__(self, candidate: Any) -> float: ...


@dataclass(frozen=True)
class RecommendationPredictionContext:
    """
    Input required to create the existing PredictionRequest.

    Prediction owns the feature/context contract. Recommendation only
    supplies the candidate identity and context.
    """

    subject_type: str
    subject_id: str
    context: dict[str, Any]


class RecommendationPredictionAdapter:
    """
    Optional bridge between the existing recommendation score and the
    existing asynchronous PredictionProvider contract.

    Important:
      - recommendation scoring remains independent;
      - prediction remains optional;
      - unavailable/disabled prediction never becomes score=0;
      - no second provider interface is introduced.
    """

    def __init__(
        self,
        *,
        base_scorer: BaseRecommendationScorer,
        prediction_provider: PredictionProvider | None = None,
        composer: RecommendationScoreComposer | None = None,
    ) -> None:
        self._base_scorer = base_scorer
        self._prediction_provider = prediction_provider
        self._composer = composer or RecommendationScoreComposer()

    async def score(
        self,
        candidate: Any,
        *,
        prediction_context: RecommendationPredictionContext | None = None,
    ) -> CombinedRecommendationScore:
        base_score = self._base_scorer(candidate)

        if not 0.0 <= base_score <= 1.0:
            raise ValueError(
                "Existing recommendation scorer returned a value outside the range 0..1"
            )

        if self._prediction_provider is None or prediction_context is None:
            return self._composer.compose(
                base_score=base_score,
                prediction_score=None,
                prediction_available=False,
            )

        request = PredictionRequest(
            subject_type=prediction_context.subject_type,
            subject_id=prediction_context.subject_id,
            context=prediction_context.context,
        )

        result = await self._prediction_provider.predict(request)

        probability = self._extract_score(result)
        available = self._is_available(result)
        confidence = self._extract_confidence(result)

        return self._composer.compose(
            base_score=base_score,
            prediction_score=probability,
            prediction_confidence=confidence,
            prediction_available=available,
        )

    @staticmethod
    def _extract_score(result: Any) -> float | None:
        score = getattr(result, "score", None)

        if score is None:
            score = getattr(result, "probability", None)

        if score is None:
            return None

        return float(score)

    @staticmethod
    def _is_available(result: Any) -> bool:
        status = getattr(result, "status", None)

        if status is not None:
            status_value = getattr(status, "value", status)

            if str(status_value).lower() in {
                "disabled",
                "unavailable",
                "not_entitled",
            }:
                return False

        available = getattr(result, "available", None)

        if available is not None:
            return bool(available)

        return getattr(result, "score", None) is not None

    @staticmethod
    def _extract_confidence(result: Any) -> float | None:
        confidence = getattr(result, "confidence", None)

        if confidence is None:
            return None

        if isinstance(confidence, (int, float)):
            return float(confidence)

        value = getattr(confidence, "value", None)

        if isinstance(value, (int, float)):
            return float(value)

        name = getattr(confidence, "name", "")

        mapping = {
            "HIGH": 0.90,
            "MEDIUM": 0.60,
            "LOW": 0.30,
        }

        return mapping.get(str(name).upper())
