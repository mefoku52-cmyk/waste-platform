"""READ-ONLY tool: compute transport route for a listing.

Uses existing routing.calculate_route() (Nominatim + OSRM).
Never creates a deal. Never reveals hidden data.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.listings.infrastructure.models import ListingsModel
from app.modules.recommendations.application.routing import calculate_route


class CmepListingTransportHandler:
    _ALLOWED: frozenset[str] = frozenset(
        {"listing_id", "from_location", "consumption", "fuel_price", "roundtrip"}
    )

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, request) -> ToolResult:
        args = dict(request.arguments or {})
        unknown = set(args) - self._ALLOWED
        if unknown:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Nepodporované argumenty: " + ", ".join(sorted(unknown)),
            )

        from_location = str(args.get("from_location") or "").strip()
        if not from_location:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Chýba parameter 'from_location' (odkiaľ).",
            )

        # Zisti ciel (bud z listing_id alebo prazdne)
        destination = None
        listing_title = None
        listing_id = str(args.get("listing_id") or "").strip()
        if listing_id:
            try:
                lid = uuid.UUID(listing_id)
            except (ValueError, TypeError):
                return ToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error_code="invalid_arguments",
                    error_message="Neplatné listing_id.",
                )
            try:
                listing = (
                    await self._session.execute(
                        select(ListingsModel).where(ListingsModel.id == lid)
                    )
                ).scalar_one_or_none()
            except Exception:
                listing = None
            if listing is None:
                return ToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    success=False,
                    error_code="listing_not_found",
                    error_message="Ponuka sa nenašla.",
                )
            destination = (listing.location or "").strip()
            listing_title = listing.title

        if not destination:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Ponuka nemá lokalitu alebo chýba listing_id.",
            )

        try:
            consumption = float(args.get("consumption", 28.0))
        except (TypeError, ValueError):
            consumption = 28.0
        try:
            fuel_price = float(args.get("fuel_price", 1.49))
        except (TypeError, ValueError):
            fuel_price = 1.49
        roundtrip = bool(args.get("roundtrip", False))

        try:
            result = await asyncio.to_thread(
                calculate_route,
                origin_text=from_location,
                destination_text=destination,
                consumption=consumption,
                fuel_price=fuel_price,
                roundtrip=roundtrip,
            )
        except Exception as exc:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="route_failed",
                error_message=str(exc)[:200] or "Routing zlyhal.",
            )

        payload: dict[str, Any] = {
            "from": from_location,
            "to": destination,
            "listing_title": listing_title,
            "distance_km": result.get("distanceKm"),
            "duration_min": result.get("durationMin"),
            "best_kind": result.get("bestKind"),
            "fuel": result.get("fuel"),
            "options": result.get("options"),
            "map_url": result.get("mapUrl"),
            "provider": result.get("provider"),
        }
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data=payload,
        )
