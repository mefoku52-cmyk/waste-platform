"""READ-ONLY user tools for CMEP agent platform.

Every tool in this module:
- Reads only data the authenticated user has access to.
- Uses identity-bound context (company_ids passed at construction).
- Never returns raw ORM objects.
- Never returns secrets.

Security model:
- Handlers receive `company_ids` and `is_platform_admin` at construction.
- Ownership checks happen inside handlers.
- Tools with listing_id validate that the caller owns the listing.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ....companies.application.services import GetCompanyService
from ....listings.application.services import ListingsService
from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


def _err(request_id: str, tool_name: str, code: str, msg: str) -> ToolResult:
    return ToolResult(
        request_id=request_id,
        tool_name=tool_name,
        success=False,
        error_code=code,
        error_message=msg,
    )


def _ok(request_id: str, tool_name: str, data: dict[str, Any]) -> ToolResult:
    return ToolResult(
        request_id=request_id,
        tool_name=tool_name,
        success=True,
        data=data,
    )


def _listing_summary(entity: Any) -> dict[str, Any]:
    """Bezpečná serializácia listing entity — žiadne ORM objekty."""
    return {
        "id": str(getattr(entity, "id", "")),
        "title": str(getattr(entity, "title", "")),
        "materialType": getattr(entity, "material_type", None),
        "quantity": getattr(entity, "quantity", None),
        "unit": getattr(entity, "unit", None),
        "location": getattr(entity, "location", None),
        "price": getattr(entity, "price", None),
        "currency": getattr(entity, "currency", None),
        "condition": getattr(entity, "condition", None),
        "status": str(
            getattr(getattr(entity, "status", None), "value", None)
            or getattr(entity, "status", None)
            or ""
        ),
        "imageUrl": getattr(entity, "image_url", None),
    }


class CmepUserToolsHandler:
    """Identity-bound READ-ONLY tools for the authenticated user."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        listings_service: ListingsService,
        get_company_service: GetCompanyService,
        company_ids: tuple[str, ...],
        is_platform_admin: bool = False,
    ) -> None:
        self._session = session
        self._listings = listings_service
        self._get_company = get_company_service
        self._company_ids = tuple(str(c) for c in (company_ids or ()))
        self._is_admin = bool(is_platform_admin)

    async def handle(self, request: ToolRequest) -> ToolResult:
        name = request.tool_name
        args = request.arguments or {}
        try:
            if name == "get_my_listings":
                return await self._my_listings(request, args)
            if name == "get_my_company":
                return await self._my_company(request, args)
            if name == "get_listing_details":
                return await self._listing_details(request, args)
            if name == "get_listing_stats":
                return await self._listing_stats(request, args)
            if name == "get_company_listings":
                return await self._company_listings(request, args)
            if name == "get_recommendations":
                return await self._recommendations(request, args)
        except Exception as exc:
            return _err(
                request.request_id,
                name,
                "tool_exception",
                f"Tool zlyhal: {type(exc).__name__}",
            )
        return _err(request.request_id, name, "unknown_tool", "Neznámy nástroj")

    # ─────────────────────────────────────────────
    async def _my_listings(self, request: ToolRequest, args: dict) -> ToolResult:
        status_filter = args.get("status")
        limit = int(args.get("limit") or 20)
        limit = max(1, min(limit, 50))

        if not self._company_ids:
            return _ok(request.request_id, request.tool_name, {"items": [], "count": 0})

        # ListingsService.list_all(page, limit, company_ids)
        try:
            items = await self._listings.list_all(1, limit, company_ids=list(self._company_ids))
        except Exception:
            return _ok(request.request_id, request.tool_name, {"items": [], "count": 0})

        summaries = [_listing_summary(e) for e in items]
        if status_filter:
            summaries = [s for s in summaries if s["status"] == str(status_filter)]
        return _ok(
            request.request_id,
            request.tool_name,
            {"items": summaries, "count": len(summaries)},
        )

    # ─────────────────────────────────────────────
    async def _my_company(self, request: ToolRequest, args: dict) -> ToolResult:
        if not self._company_ids:
            return _ok(request.request_id, request.tool_name, {"company": None})
        try:
            dto = await self._get_company.execute(UUID(self._company_ids[0]))
        except Exception:
            return _ok(request.request_id, request.tool_name, {"company": None})
        return _ok(
            request.request_id,
            request.tool_name,
            {
                "company": {
                    "id": str(getattr(dto, "id", "")),
                    "legalName": getattr(dto, "legal_name", None),
                    "tradingName": getattr(dto, "trading_name", None),
                    "city": getattr(dto, "city", None),
                    "status": str(
                        getattr(getattr(dto, "status", None), "value", None)
                        or getattr(dto, "status", None)
                        or ""
                    ),
                    "subscriptionTier": str(
                        getattr(getattr(dto, "subscription_tier", None), "value", None)
                        or getattr(dto, "subscription_tier", None)
                        or ""
                    ),
                }
            },
        )

    # ─────────────────────────────────────────────
    def _can_access_listing(self, entity: Any) -> bool:
        owner = str(getattr(entity, "company_id", "") or "")
        if self._is_admin:
            return True
        return owner in self._company_ids

    async def _listing_details(self, request: ToolRequest, args: dict) -> ToolResult:
        listing_id = str(args.get("listing_id") or "").strip()
        if not listing_id:
            return _err(request.request_id, request.tool_name, "missing_arg", "listing_id chýba")
        entity = await self._listings.get_by_id(listing_id)
        if entity is None:
            return _err(request.request_id, request.tool_name, "not_found", "Ponuka neexistuje")
        if not self._can_access_listing(entity):
            return _err(request.request_id, request.tool_name, "forbidden", "Nemáš prístup")
        return _ok(request.request_id, request.tool_name, {"listing": _listing_summary(entity)})

    # ─────────────────────────────────────────────
    async def _listing_stats(self, request: ToolRequest, args: dict) -> ToolResult:
        listing_id = str(args.get("listing_id") or "").strip()
        if not listing_id:
            return _err(request.request_id, request.tool_name, "missing_arg", "listing_id chýba")
        try:
            stats = await self._listings.get_stats(
                listing_id,
                owner_company_ids=set(self._company_ids) if not self._is_admin else None,
            )
        except Exception as exc:
            msg = str(exc)
            if "vlastník" in msg.lower() or "forbidden" in msg.lower():
                return _err(request.request_id, request.tool_name, "forbidden", msg)
            return _err(request.request_id, request.tool_name, "stats_failed", "Nepodarilo sa")
        return _ok(request.request_id, request.tool_name, {"stats": stats})

    # ─────────────────────────────────────────────
    async def _company_listings(self, request: ToolRequest, args: dict) -> ToolResult:
        company_id = str(args.get("company_id") or "").strip()
        limit = int(args.get("limit") or 20)
        limit = max(1, min(limit, 50))
        if not company_id:
            return _err(request.request_id, request.tool_name, "missing_arg", "company_id chýba")
        try:
            items = await self._listings.list_all(1, limit, company_ids=[company_id])
        except Exception:
            return _ok(request.request_id, request.tool_name, {"items": [], "count": 0})
        # Filtruj iba published (verejné)
        summaries = [_listing_summary(e) for e in items]
        summaries = [s for s in summaries if s["status"] == "published"]
        return _ok(
            request.request_id,
            request.tool_name,
            {"items": summaries, "count": len(summaries)},
        )

    # ─────────────────────────────────────────────
    async def _recommendations(self, request: ToolRequest, args: dict) -> ToolResult:
        listing_id = str(args.get("listing_id") or "").strip()
        if not listing_id:
            return _err(request.request_id, request.tool_name, "missing_arg", "listing_id chýba")
        try:
            from ....recommendations.application.service import RecommendationsService

            svc = RecommendationsService(self._session)
            result = await svc.list_for_listing(UUID(listing_id))
        except Exception:
            return _ok(
                request.request_id,
                request.tool_name,
                {"recommendations": None, "note": "Odporúčania nie sú dostupné."},
            )
        if not isinstance(result, dict):
            result = {}
        safe = {
            "buyers": list(result.get("buyers") or [])[:10],
            "carriers": list(result.get("carriers") or [])[:5],
        }
        return _ok(request.request_id, request.tool_name, {"recommendations": safe})
