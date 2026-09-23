"""Attach prediction status to existing recommendation items.

Production rule for this wiring:
- score_company remains the source of `score`
- this module never writes 0 as a substitute for disabled/locked/unavailable
- first production status comes from config + factory entitlement
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.modules.prediction.application.config import PredictionConfig
from app.modules.prediction.application.factory import create_prediction_service

ALLOWED_STATUS = frozenset({"active", "disabled", "unavailable", "locked"})


def _as_status(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    name = str(getattr(value, "value", value)).strip().lower()
    if name in {"available"}:
        name = "active"
    if name in {"off"}:
        name = "disabled"
    if name in ALLOWED_STATUS:
        return name
    return fallback


def _config_enabled(config: PredictionConfig) -> bool | None:
    for attr in (
        "enabled",
        "service_enabled",
        "prediction_enabled",
        "PREDICTION_SERVICE_ENABLED",
    ):
        if hasattr(config, attr):
            return bool(getattr(config, attr))
    data = getattr(config, "__dict__", {})
    for key, raw in data.items():
        if "enable" in str(key).lower():
            return bool(raw)
    return None


def _pick_score(item: Mapping[str, Any]) -> float | None:
    raw = item.get("score")
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


async def resolve_prediction_status() -> str:
    """Map runtime config + default factory entitlement to API status."""
    try:
        config = PredictionConfig.from_environment()
    except Exception:
        return "unavailable"

    enabled = _config_enabled(config)
    if enabled is None:
        return "unavailable"
    if enabled is False:
        return "disabled"

    try:
        service = create_prediction_service()
    except Exception:
        return "unavailable"

    entitlement = getattr(service, "_entitlement_provider", None)
    if entitlement is None:
        entitlement = getattr(service, "entitlement_provider", None)
    if entitlement is not None and hasattr(entitlement, "has_prediction_access"):
        try:
            entitled = await entitlement.has_prediction_access(None)
        except TypeError:
            try:
                entitled = await entitlement.has_prediction_access()
            except Exception:
                entitled = False
        except Exception:
            entitled = False
        if not entitled:
            return "locked"

    availability = None
    provider = getattr(service, "_provider", None)
    if provider is None:
        provider = getattr(service, "provider", None)
    if provider is not None and hasattr(provider, "availability"):
        try:
            availability = provider.availability()
        except Exception:
            availability = None
    return _as_status(availability, "locked")


async def enrich_recommendation_item(item: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(item)
    rule_score = _pick_score(out)
    out["rule_score"] = rule_score
    out["prediction_score"] = None
    out["prediction_applied"] = False
    out["prediction_status"] = await resolve_prediction_status()

    if rule_score is not None:
        out["score"] = rule_score
    return out


async def enrich_recommendation_items(
    items: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not items:
        return []
    status = await resolve_prediction_status()
    enriched: list[dict[str, Any]] = []
    for item in items:
        out = dict(item)
        rule_score = _pick_score(out)
        out["rule_score"] = rule_score
        out["prediction_score"] = None
        out["prediction_applied"] = False
        out["prediction_status"] = status
        if rule_score is not None:
            out["score"] = rule_score
        enriched.append(out)
    return enriched
