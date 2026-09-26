"""Real handler for cmep.company.search – calls the CMEP company service."""

from __future__ import annotations

from typing import Any

from app.modules.agent_platform.domain.tools.tool_result import ToolResult


class CmepCompanySearchHandler:
    """Search CMEP companies through the existing service.

    Only authenticated actors may search. Scope is enforced by the
    application boundary (company_ids / admin flag).
    """

    _ALLOWED: frozenset[str] = frozenset(
        {
            "q",
            "company_type",
            "seller_capability",
            "buyer_capability",
            "logistics_capability",
            "page",
            "page_size",
        }
    )

    def __init__(
        self,
        *,
        service,
        is_platform_admin: bool,
        company_ids: tuple[str, ...],
    ) -> None:
        self._service = service
        self._is_platform_admin = bool(is_platform_admin)
        self._company_ids = tuple(company_ids)

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

        company_scope: list[str] | None
        if self._is_platform_admin:
            company_scope = None
        elif self._company_ids:
            company_scope = list(self._company_ids)
        else:
            # Authenticated but not member of any company – see nothing.
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="company_access_denied",
                error_message="Najprv si vytvor alebo over firmu.",
            )

        try:
            items, total = await self._service.execute(
                status=None,
                company_type=args.get("company_type"),
                seller_capability=args.get("seller_capability"),
                buyer_capability=args.get("buyer_capability"),
                logistics_capability=args.get("logistics_capability"),
                q=args.get("q"),
                page=page,
                page_size=page_size,
                company_ids=company_scope,
            )
        except Exception as exc:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="company_search_failed",
                error_message=f"Chyba vyhľadávania: {type(exc).__name__}",
            )

        serialized: list[dict[str, Any]] = []
        for item in items:
            serialized.append(
                {
                    "id": str(getattr(item, "id", "")),
                    "legal_name": getattr(item, "legal_name", None),
                    "trading_name": getattr(item, "trading_name", None),
                    "city": getattr(item, "city", None),
                    "country_code": getattr(item, "country_code", None),
                    "company_type": getattr(item, "company_type", None),
                    "status": getattr(item, "status", None),
                    "seller_capability": getattr(item, "seller_capability", None),
                    "buyer_capability": getattr(item, "buyer_capability", None),
                    "logistics_capability": getattr(item, "logistics_capability", None),
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
