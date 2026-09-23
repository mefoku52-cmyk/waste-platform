"""Static initial tool catalog.

Only declarations live here.

There are intentionally no executable handlers in Phase 2.
"""

from ...domain.tools.tool_definition import ToolDefinition
from ...domain.tools.tool_risk import ToolRisk


def build_initial_tool_catalog() -> tuple[ToolDefinition, ...]:
    """Return explicitly approved conceptual tool definitions.

    These tools are NOT registered automatically into production yet.
    They describe the future boundary only.
    """

    return (
        ToolDefinition(
            name="cmep.user.get_profile",
            description="Read the current authenticated user's profile.",
            domain="users",
            action="read",
            risk=ToolRisk.LOW,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.company.search",
            description="Search CMEP companies through the company service.",
            domain="companies",
            action="search",
            risk=ToolRisk.LOW,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.listing.search",
            description="Search marketplace listings through the listing service.",
            domain="listings",
            action="search",
            risk=ToolRisk.LOW,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.inquiry.prepare",
            description="Prepare an inquiry without sending it.",
            domain="inquiries",
            action="prepare",
            risk=ToolRisk.MEDIUM,
            requires_approval=False,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.inquiry.send",
            description="Send an inquiry through the existing inquiry service.",
            domain="inquiries",
            action="send",
            risk=ToolRisk.HIGH,
            requires_approval=True,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.notifications.read",
            description="Read notifications available to the authenticated actor.",
            domain="notifications",
            action="read",
            risk=ToolRisk.LOW,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.prediction.read",
            description="Request an existing prediction through its provider contract.",
            domain="prediction",
            action="read",
            risk=ToolRisk.MEDIUM,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="cmep.recommendations.read",
            description="Read existing recommendation results.",
            domain="recommendations",
            action="read",
            risk=ToolRisk.LOW,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
        ToolDefinition(
            name="external.web.search",
            description="Search the public web through an approved external gateway.",
            domain="external_web",
            action="search",
            risk=ToolRisk.MEDIUM,
            allowed_actor_types=frozenset({"user", "admin", "ai"}),
        ),
    )
