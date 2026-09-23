"""Phase 2: attach prediction beside score_company."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.modules.prediction.application.baseline_provider import (
    BaselinePredictionProvider,
)
from app.modules.prediction.application.recommendation_adapter import (
    RecommendationPredictionAdapter,
    RecommendationPredictionContext,
)
from app.modules.prediction.application.recommendation_composer import (
    RecommendationScoreComposer,
)


class _FixedScorer:
    def __init__(self, score: float) -> None:
        self._score = score

    def __call__(self, candidate: Any) -> float:
        return self._score


def _pick_score(item: Mapping[str, Any]) -> float | None:
    raw = item.get("score")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _empty(rule_score: float | None) -> dict[str, Any]:
    return {
        "rule_score": rule_score,
        "prediction_score": None,
        "combined_score": None,
        "prediction_applied": False,
        "prediction_status": "unavailable",
    }


def _context(item: Mapping[str, Any]) -> RecommendationPredictionContext:
    subject_id = item.get("companyId") or item.get("company_id") or "unknown"
    return RecommendationPredictionContext(
        subject_type="company",
        subject_id=str(subject_id),
        context={
            "score": item.get("score"),
            "reasons": item.get("reasons") or [],
            "city": item.get("city"),
            "listing_views": item.get("listing_views", 0),
        },
    )


def _from_combined(result: Any, rule_score: float) -> dict[str, Any]:
    pred = getattr(result, "prediction_score", None)
    applied = bool(getattr(result, "prediction_applied", False))
    combined = getattr(result, "final_score", None)
    if combined is None:
        combined = getattr(result, "combined_score", None)
    if combined is None:
        combined = getattr(result, "score", None)
    status = "active" if applied else "unavailable"
    pred_out = float(pred) if isinstance(pred, (int, float)) else None
    if pred_out == 0.0 and not applied:
        pred_out = None
        status = "unavailable"
    return {
        "rule_score": rule_score,
        "prediction_score": pred_out,
        "combined_score": (float(combined) if isinstance(combined, (int, float)) else None),
        "prediction_applied": applied,
        "prediction_status": status,
    }


async def predict_one(rule_score: float, item: Mapping[str, Any]) -> dict[str, Any]:
    adapter = RecommendationPredictionAdapter(
        base_scorer=_FixedScorer(rule_score),
        prediction_provider=BaselinePredictionProvider(),
        composer=RecommendationScoreComposer(),
    )
    result = await adapter.score(item, prediction_context=_context(item))
    return _from_combined(result, rule_score)


async def enrich_recommendation_item(item: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(item)
    rule_score = _pick_score(out)
    extra = await predict_one(rule_score, out) if rule_score is not None else _empty(None)
    out.update(extra)
    if rule_score is not None:
        out["score"] = rule_score
        out["rule_score"] = rule_score
    return out


async def enrich_recommendation_items(
    items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [await enrich_recommendation_item(item) for item in items]
