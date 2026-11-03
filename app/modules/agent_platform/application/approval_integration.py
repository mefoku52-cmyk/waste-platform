"""Deterministic server-side risk classification for AI tools.

Unknown tools are treated as HIGH_RISK (fail-closed).
"""

from __future__ import annotations

from app.modules.agent_platform.application.approval_service import RiskLevel

# Explicit write tools that require approval
WRITE_TOOLS_REQUIRING_APPROVAL = {
    "update_listing",
    "publish_listing",
    "create_inquiry",
    "update_inquiry_status",
    "promote_listing",
    "delete_listing",
    "cancel_inquiry",
}

# Explicit read-only tools
READ_ONLY_TOOLS = {
    "get_listing",
    "list_listings",
    "get_inquiry",
    "list_inquiries",
    "get_company",
    "search_listings",
}


def classify_risk(tool_name: str) -> RiskLevel:
    """Server-side only. Unknown tools fail closed."""
    if tool_name in READ_ONLY_TOOLS:
        return RiskLevel.READ_ONLY
    if tool_name in WRITE_TOOLS_REQUIRING_APPROVAL:
        return RiskLevel.HIGH_RISK
    if tool_name.startswith("get_") or tool_name.startswith("list_") or tool_name.startswith("search_"):
        return RiskLevel.READ_ONLY
    # Fail closed
    return RiskLevel.HIGH_RISK