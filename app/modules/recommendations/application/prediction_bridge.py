"""Optional prediction metadata for existing recommendation items.

Does not replace score_company.
Disabled/locked/unavailable must not become score 0.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _pick_score(item: Mapping[str, Any]) -> float | None:
    raw = item.get("score")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


async def enrich_recommendation_item(item: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(item)
    rule_score = _pick_score(out)
    out["rule_score"] = rule_score
    out["prediction_score"] = None
    out["prediction_applied"] = False
    out["prediction_status"] = "disabled"

    if rule_score is None:
        out["prediction_status"] = "unavailable"
        return out

    try:
        from app.modules.prediction.application.config import PredictionConfig
        from app.modules.prediction.application.factory import (
            create_prediction_service,
        )

        config = PredictionConfig.from_environment()
        enabled = bool(getattr(config, "enabled", False))
        if hasattr(config, "PREDICTION_SERVICE_ENABLED"):
            enabled = bool(config.PREDICTION_SERVICE_ENABLED)
        for attr in ("enabled", "prediction_enabled", "service_enabled"):
            if hasattr(config, attr):
                enabled = bool(getattr(config, attr))
                break

        service = create_prediction_service()
        # Default factory uses DisabledPredictionEntitlementProvider.
        # Do not compute or overwrite score in this first wiring.
        if not enabled:
            out["prediction_status"] = "disabled"
        else:
            out["prediction_status"] = "locked"

        _ = service
        if "score" in out:
            out["score"] = float(rule_score)
    except Exception:
        out["prediction_status"] = "unavailable"
        out["prediction_score"] = None
        out["prediction_applied"] = False
        if rule_score is not None and "score" in out:
            out["score"] = float(rule_score)
    return out


async def enrich_recommendation_items(
    items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [await enrich_recommendation_item(item) for item in items]
