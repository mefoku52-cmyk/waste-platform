"""Read-only admin tools for the platform architect.

These tools are ONLY registered when the caller is a platform admin.
They never write, never mutate, never expose secrets.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.domain.tools.tool_result import ToolResult


class CmepAdminToolsHandler:
    """A single handler factory for all admin read tools.

    Each tool has its own method. The dispatcher routes by tool_name.
    """

    _ALLOWED_BY_TOOL: dict[str, frozenset[str]] = {
        "get_platform_stats": frozenset(),
        "get_recent_activity": frozenset({"days", "limit"}),
        "get_companies_with_tiers": frozenset({"tier", "limit"}),
        "get_my_company_context": frozenset(),
    }

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, request) -> ToolResult:
        tool_name = request.tool_name
        allowed = self._ALLOWED_BY_TOOL.get(tool_name)
        if allowed is None:
            return ToolResult(
                request_id=request.request_id,
                tool_name=tool_name,
                success=False,
                error_code="unknown_admin_tool",
                error_message=f"Not an admin tool: {tool_name}",
            )

        args = dict(request.arguments or {})
        unknown = set(args) - allowed
        if unknown:
            return ToolResult(
                request_id=request.request_id,
                tool_name=tool_name,
                success=False,
                error_code="invalid_arguments",
                error_message="Nepodporované argumenty: " + ", ".join(sorted(unknown)),
            )

        try:
            if tool_name == "get_platform_stats":
                data = await self._stats()
            elif tool_name == "get_recent_activity":
                data = await self._recent_activity(args)
            elif tool_name == "get_companies_with_tiers":
                data = await self._companies_tiers(args)
            elif tool_name == "get_my_company_context":
                data = await self._my_context()
            else:
                raise RuntimeError("unreachable")
        except Exception as exc:
            return ToolResult(
                request_id=request.request_id,
                tool_name=tool_name,
                success=False,
                error_code="admin_tool_failed",
                error_message=f"{type(exc).__name__}: {exc}",
            )

        return ToolResult(
            request_id=request.request_id,
            tool_name=tool_name,
            success=True,
            data=data,
        )

    async def _stats(self) -> dict[str, Any]:
        rows = {}
        for label, sql in (
            ("companies", "SELECT COUNT(*) FROM companies"),
            ("listings", "SELECT COUNT(*) FROM listings"),
            ("users", "SELECT COUNT(*) FROM users"),
            ("inquiries", "SELECT COUNT(*) FROM inquiries"),
            ("documents", "SELECT COUNT(*) FROM documents"),
            ("ai_conversations", "SELECT COUNT(*) FROM ai_conversations"),
            ("ai_messages", "SELECT COUNT(*) FROM ai_messages"),
        ):
            try:
                r = await self._session.execute(text(sql))
                rows[label] = int(r.scalar() or 0)
            except Exception:
                rows[label] = None
        return {"stats": rows}

    async def _recent_activity(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            days = int(args.get("days", 7))
        except (TypeError, ValueError):
            days = 7
        try:
            limit = int(args.get("limit", 30))
        except (TypeError, ValueError):
            limit = 30
        days = max(1, min(days, 30))
        limit = max(1, min(limit, 100))

        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
        sql = text(
            """
            SELECT event_type, actor_user_id, company_id, listing_id, payload, created_at
            FROM activity_events
            WHERE created_at >= :cutoff
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        try:
            r = await self._session.execute(sql, {"cutoff": cutoff, "limit": limit})
            items = [
                {
                    "event_type": row[0],
                    "actor_user_id": row[1],
                    "company_id": row[2],
                    "listing_id": row[3],
                    "payload": (row[4] or "")[:200],
                    "created_at": row[5].isoformat() if row[5] else None,
                }
                for row in r
            ]
        except Exception as exc:
            return {"error": f"activity_query_failed: {type(exc).__name__}"}
        return {"days": days, "count": len(items), "items": items}

    async def _companies_tiers(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_tier = str(args.get("tier") or "").strip().lower()
        tier_filter = raw_tier if raw_tier in {"free", "pro", "ai"} else None
        try:
            limit = int(args.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, 100))

        if tier_filter:
            sql = text(
                """
                SELECT legal_name, city, status, subscription_tier
                FROM companies
                WHERE subscription_tier = :tier
                ORDER BY legal_name
                LIMIT :limit
                """
            )
            params = {"tier": tier_filter, "limit": limit}
        else:
            sql = text(
                """
                SELECT legal_name, city, status, subscription_tier
                FROM companies
                ORDER BY legal_name
                LIMIT :limit
                """
            )
            params = {"limit": limit}

        try:
            r = await self._session.execute(sql, params)
            items = [
                {
                    "legal_name": row[0],
                    "city": row[1],
                    "status": row[2],
                    "subscription_tier": row[3] or "free",
                }
                for row in r
            ]
        except Exception as exc:
            return {"error": f"tiers_query_failed: {type(exc).__name__}"}
        return {"tier_filter": tier_filter, "count": len(items), "items": items}

    async def _my_context(self) -> dict[str, Any]:
        # Bez company_id v request kontexte vratime prehlad vsetkych firiem.
        sql = text(
            """
            SELECT legal_name, city, status, subscription_tier
            FROM companies
            ORDER BY created_at ASC
            """
        )
        try:
            r = await self._session.execute(sql)
            rows = list(r)
        except Exception as exc:
            return {"error": f"context_query_failed: {type(exc).__name__}"}
        return {
            "count": len(rows),
            "companies": [
                {
                    "legal_name": row[0],
                    "city": row[1],
                    "status": row[2],
                    "subscription_tier": row[3] or "free",
                }
                for row in rows
            ],
        }
