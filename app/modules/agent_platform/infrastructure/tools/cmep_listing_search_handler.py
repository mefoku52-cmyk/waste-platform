"""Real handler for cmep.listing.search – calls the CMEP listings service."""

from __future__ import annotations

from typing import Any

from app.modules.agent_platform.domain.tools.tool_result import ToolResult


class CmepListingSearchHandler:
    _ALLOWED: frozenset[str] = frozenset({"q", "material_type", "location", "page", "page_size"})

    def __init__(self, *, service) -> None:
        self._service = service

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

        try:
            page = int(args.get("page", 1))
            page_size = int(args.get("page_size", 10))
        except (TypeError, ValueError):
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="page/page_size musia byť čísla.",
            )

        if page < 1 or page_size < 1 or page_size > 50:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Neplatné page/page_size.",
            )

        try:
            result = await self._service.list_marketplace(
                page=page,
                limit=page_size,
                q=args.get("q"),
                material_type=args.get("material_type"),
                location=args.get("location"),
            )
        except Exception as exc:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="listing_search_failed",
                error_message=f"Chyba vyhľadávania: {type(exc).__name__}",
            )

        items = result[0] if isinstance(result, tuple) else result
        total = result[1] if isinstance(result, tuple) and len(result) > 1 else len(items or [])

        serialized: list[dict[str, Any]] = []
        for item in items or []:
            serialized.append(
                {
                    "id": str(getattr(item, "id", "")),
                    "title": getattr(item, "title", None),
                    "material_type": getattr(item, "material_type", None),
                    "location": getattr(item, "location", None),
                    "quantity": getattr(item, "quantity", None),
                    "unit": getattr(item, "unit", None),
                    "status": getattr(item, "status", None),
                }
            )

        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={
                "items": serialized,
                "total": total,
                "page": page,
                "page_size": page_size,
            },
        )
