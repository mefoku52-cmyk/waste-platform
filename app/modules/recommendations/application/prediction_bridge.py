"""Phase 2: attach prediction beside score_company.

`score` stays the original rule score.
Unavailable prediction never becomes 0.
Entitlement is not decided here.
"""

from __future__ import annotations

import inspect
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


def _pick_score(item: Mapping[str, Any]) -> float | None:
    raw = item.get("score")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _status_from(obj: Any, fallback: str) -> str:
    if obj is None:
        return fallback
    for attr in ("status", "availability", "prediction_status"):
        raw = getattr(obj, attr, None)
        if raw is None:
            continue
        name = str(getattr(raw, "value", raw)).strip().lower()
        if name == "available":
            name = "active"
        if name in {"active", "disabled", "unavailable", "locked"}:
            return name
    return fallback


class _FixedScorer:
    def __init__(self, score: float) -> None:
        self._score = score

    def score_company(self, *args: Any, **kwargs: Any) -> float:
        return self._score

    def score(self, *args: Any, **kwargs: Any) -> float:
        return self._score

    def __call__(self, *args: Any, **kwargs: Any) -> float:
        return self._score


def _build_context(item: Mapping[str, Any]) -> Any:
    fields = list(getattr(RecommendationPredictionContext, "__annotations__", {}).keys())
    payload: dict[str, Any] = {}
    aliases = {
        "listing_id": ("listingId", "listing_id"),
        "listingId": ("listingId", "listing_id"),
        "company_id": ("companyId", "company_id"),
        "companyId": ("companyId", "company_id"),
        "subject_id": ("companyId", "company_id", "listingId"),
        "subject_type": (),
        "context": (),
        "listing_views": ("listing_views",),
        "city": ("city",),
    }
    for field in fields:
        if field == "subject_type":
            payload[field] = "company"
            continue
        if field == "context":
            payload[field] = {
                "score": item.get("score"),
                "reasons": item.get("reasons") or [],
                "city": item.get("city"),
            }
            continue
        for key in aliases.get(field, (field,)):
            if key in item:
                payload[field] = item[key]
                break
    try:
        return RecommendationPredictionContext(**payload)
    except TypeError:
        return None


def _empty(rule_score: float | None) -> dict[str, Any]:
    return {
        "rule_score": rule_score,
        "prediction_score": None,
        "combined_score": None,
        "prediction_applied": False,
        "prediction_status": "unavailable",
    }


async def _call_adapter(adapter: Any, ctx: Any, rule_score: float) -> Any:
    call = None
    for name in ("enrich", "score", "combine", "apply", "recommend", "__call__"):
        if hasattr(adapter, name):
            call = getattr(adapter, name)
            break
    if call is None:
        return None
    try:
        result = call(ctx) if ctx is not None else call(rule_score)
        if inspect.isawaitable(result):
            result = await result
        return result
    except TypeError:
        try:
            result = call(rule_score, ctx)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception:
            return None
    except Exception:
        return None


async def _predict_one(rule_score: float, item: Mapping[str, Any]) -> dict[str, Any]:
    out = _empty(rule_score)
    try:
        adapter = RecommendationPredictionAdapter(
            base_scorer=_FixedScorer(rule_score),
            prediction_provider=BaselinePredictionProvider(),
            composer=RecommendationScoreComposer(),
        )
        result = await _call_adapter(adapter, _build_context(item), rule_score)
        if result is None:
            return out
        pred = getattr(result, "prediction_score", None)
        applied = bool(getattr(result, "prediction_applied", False))
        combined = getattr(result, "final_score", None)
        if combined is None:
            combined = getattr(result, "combined_score", None)
        if combined is None:
            combined = getattr(result, "score", None)
        status = _status_from(result, "unavailable")
        if applied:
            status = "active"
        out["prediction_score"] = float(pred) if isinstance(pred, (int, float)) else None
        out["prediction_applied"] = applied
        out["combined_score"] = float(combined) if isinstance(combined, (int, float)) else None
        out["prediction_status"] = status
        if out["prediction_score"] == 0.0 and not applied:
            out["prediction_score"] = None
            out["prediction_status"] = "unavailable"
        return out
    except Exception:
        return out


async def enrich_recommendation_item(item: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(item)
    rule_score = _pick_score(out)
    extra = await _predict_one(rule_score, out) if rule_score is not None else _empty(None)
    out.update(extra)
    if rule_score is not None:
        out["score"] = rule_score
        out["rule_score"] = rule_score
    return out


async def enrich_recommendation_items(
    items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [await enrich_recommendation_item(item) for item in items]
