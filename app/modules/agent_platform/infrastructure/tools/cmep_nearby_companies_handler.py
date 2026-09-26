"""READ-ONLY tool: search companies near a location.

Uses the existing RecommendationsService + CompanyRepository.
Never writes. Never mutates. Never reveals hidden contacts.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.companies.domain.enums import CompanyStatus
from app.modules.companies.infrastructure.models import CompanyModel


class CmepNearbyCompaniesHandler:
    _ALLOWED: frozenset[str] = frozenset(
        {"near", "buyer_capability", "seller_capability", "material_type", "limit"}
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

        near = str(args.get("near") or "").strip()
        if not near:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Chýba parameter 'near' (mesto alebo región).",
            )

        try:
            limit = int(args.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 50))

        stmt = select(CompanyModel).where(
            CompanyModel.status == CompanyStatus.VERIFIED.value,
        )

        if args.get("buyer_capability") is True:
            stmt = stmt.where(CompanyModel.buyer_capability.is_(True))
        if args.get("seller_capability") is True:
            stmt = stmt.where(CompanyModel.seller_capability.is_(True))

        material = str(args.get("material_type") or "").strip().lower()
        if material:
            stmt = stmt.where(CompanyModel.accepted_material_types.ilike(f"%{material}%"))

        stmt = stmt.limit(limit * 5)

        try:
            rows = list((await self._session.execute(stmt)).scalars().all())
        except Exception as exc:
            return ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_code="nearby_search_failed",
                error_message=f"DB chyba: {type(exc).__name__}",
            )

        needle = near.casefold()
        matched: list[dict[str, Any]] = []
        for c in rows:
            city = (c.city or "").casefold()
            name = (c.legal_name or "").casefold()
            if needle in city or needle in name:
                matched.append(
                    {
                        "id": str(c.id),
                        "legal_name": c.legal_name,
                        "city": c.city,
                        "country_code": c.country_code,
                        "company_type": c.company_type,
                        "buyer_capability": bool(c.buyer_capability),
                        "seller_capability": bool(c.seller_capability),
                        "logistics_capability": bool(c.logistics_capability),
                        "accepted_material_types": c.accepted_material_types,
                    }
                )
            if len(matched) >= limit:
                break

        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={
                "near": near,
                "material_type": material or None,
                "count": len(matched),
                "items": matched,
            },
        )
