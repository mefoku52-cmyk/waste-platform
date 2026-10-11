"""Tests for the UI card builder + orchestrator card collection.

Covers:
* shape mapping for every card-producing tool (listing / company / stats);
* internal-route derivation and id validation (no unsafe href ever);
* caps and dedup;
* orchestrator wiring: cards are collected from successful tools only, and a
  builder failure never breaks the tool call.
"""

from __future__ import annotations

import pytest

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    MAX_TOTAL_CARDS,
    AgentOrchestrator,
)
from app.modules.agent_platform.application.agent.card_builder import (
    MAX_CARDS,
    build_cards,
)
from app.modules.agent_platform.domain.tools.tool_result import ToolResult
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

# ─── build_cards: mapping ───────────────────────────────────────────────────


def test_search_listings_snake_case() -> None:
    data = {
        "items": [
            {
                "id": "abc-123",
                "title": "Drevo",
                "material_type": "wood",
                "location": "Zilina",
                "quantity": 25,
                "unit": "t",
                "status": "published",
                "extra": "ignored",
            }
        ],
        "total": 1,
    }
    cards = build_cards("search_listings", data)
    assert len(cards) == 1
    card = cards[0]
    assert card["type"] == "listing"
    assert card["id"] == "abc-123"
    assert card["title"] == "Drevo"
    assert card["href"] == "/dashboard/listings/abc-123"
    assert "wood" in card["subtitle"]
    assert "Zilina" in card["subtitle"]
    assert "25 t" in card["subtitle"]
    assert card["status"] == "published"


def test_get_my_listings_camel_case_with_image() -> None:
    data = {
        "items": [
            {
                "id": "id_1",
                "title": "Kovy",
                "materialType": "metal",
                "quantity": 5,
                "unit": "kg",
                "location": "Bratislava",
                "price": 100,
                "currency": "EUR",
                "status": "draft",
                "imageUrl": "https://cdn.example/x.png",
            }
        ],
        "count": 1,
    }
    cards = build_cards("get_my_listings", data)
    assert len(cards) == 1
    card = cards[0]
    assert card["href"] == "/dashboard/listings/id_1"
    assert card["image"] == "https://cdn.example/x.png"
    assert "100 EUR" in card["subtitle"]


def test_search_companies() -> None:
    data = {
        "items": [
            {
                "id": "comp-9",
                "legal_name": "Acme s.r.o.",
                "trading_name": "Acme",
                "city": "Nitra",
                "country_code": "SK",
                "company_type": "sro",
                "status": "verified",
            }
        ]
    }
    cards = build_cards("search_companies", data)
    assert len(cards) == 1
    card = cards[0]
    assert card["type"] == "company"
    assert card["title"] == "Acme"  # trading_name preferred
    assert card["href"] == "/dashboard/companies/comp-9"
    assert "Nitra" in card["subtitle"]


def test_get_my_company_single() -> None:
    data = {"company": {"id": "c1", "legalName": "Firma s.r.o.", "city": "Kosice"}}
    cards = build_cards("get_my_company", data)
    assert len(cards) == 1
    assert cards[0]["href"] == "/dashboard/companies/c1"
    assert cards[0]["title"] == "Firma s.r.o."


def test_get_listing_details_single() -> None:
    data = {"listing": {"id": "L1", "title": "Papier", "location": "Trnava"}}
    cards = build_cards("get_listing_details", data)
    assert len(cards) == 1
    assert cards[0]["href"] == "/dashboard/listings/L1"


def test_platform_stats_card_has_no_href() -> None:
    cards = build_cards("get_platform_stats", {"stats": {"companies": 3, "listings": None}})
    assert len(cards) == 1
    card = cards[0]
    assert card["type"] == "stats"
    assert card["href"] is None
    assert {m["label"] for m in card["meta"]} == {"companies", "listings"}
    # None values are rendered as an em dash, never as "None".
    assert any(m["value"] == "—" for m in card["meta"])


# ─── build_cards: safety / edge cases ───────────────────────────────────────


def test_unknown_tool_and_bad_shape_yield_no_cards() -> None:
    assert build_cards("project_read_file", {"x": 1}) == []
    assert build_cards("search_listings", None) == []
    assert build_cards("search_listings", {"items": "not-a-list"}) == []


def test_item_without_safe_id_is_skipped() -> None:
    assert build_cards("search_listings", {"items": [{"title": "no id"}]}) == []
    # Path-traversal-ish id must be rejected (no href leaks).
    assert build_cards("search_companies", {"items": [{"id": "../x", "legal_name": "x"}]}) == []


def test_card_cap_is_enforced() -> None:
    items = [{"id": f"id-{i}", "title": f"t{i}"} for i in range(MAX_CARDS + 10)]
    cards = build_cards("search_listings", {"items": items})
    assert len(cards) == MAX_CARDS


# ─── Orchestrator wiring ────────────────────────────────────────────────────


class _Handler:
    def __init__(self, result: ToolResult) -> None:
        self._result = result

    async def handle(self, request) -> ToolResult:
        return self._result


class _Gateway:
    """Emits a fixed list of tool calls, then a final text answer."""

    def __init__(self, calls: list[tuple[str, str]]) -> None:
        self._calls = list(calls)
        self._index = 0

    def provider_name(self) -> str:
        return "fake"

    async def generate(self, request) -> ModelResponse:
        if self._index < len(self._calls):
            name, arguments = self._calls[self._index]
            self._index += 1
            return ModelResponse(
                request_id=request.request_id,
                text="",
                finish_reason="tool_calls",
                tool_calls=(
                    {
                        "id": f"call_{self._index}",
                        "type": "function",
                        "function": {"name": name, "arguments": arguments},
                    },
                ),
            )
        return ModelResponse(
            request_id=request.request_id,
            text="Hotovo.",
            finish_reason="stop",
            tool_calls=(),
        )


def _orch(gateway: _Gateway, handler: _Handler) -> AgentOrchestrator:
    from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
        ActorToolPermissionEngine,
    )
    from app.modules.agent_platform.infrastructure.policy.allowlist_policy_engine import (
        AllowlistPolicyEngine,
    )

    tool_name = "search_listings"
    scopes = {tool_name: ("listings", "search")}
    return AgentOrchestrator(
        gateway=gateway,
        tool_schemas=(),
        tool_handlers={tool_name: handler},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({tool_name})),
        permission=ActorToolPermissionEngine(
            allowed_actor_types=frozenset({"user", "admin"}),
            allowed_scopes=frozenset(scopes.values()),
        ),
        tool_scopes=scopes,
        card_builder=build_cards,
    )


@pytest.mark.asyncio
async def test_orchestrator_collects_cards_from_successful_tool() -> None:
    handler = _Handler(
        ToolResult(
            request_id="r",
            tool_name="search_listings",
            success=True,
            data={"items": [{"id": "L1", "title": "Drevo"}]},
        )
    )
    orch = _orch(_Gateway([("search_listings", "{}")]), handler)

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert len(result.cards) == 1
    assert result.cards[0]["href"] == "/dashboard/listings/L1"


@pytest.mark.asyncio
async def test_orchestrator_no_cards_from_failed_tool() -> None:
    handler = _Handler(
        ToolResult(
            request_id="r",
            tool_name="search_listings",
            success=False,
            error_code="boom",
        )
    )
    orch = _orch(_Gateway([("search_listings", "{}")]), handler)

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert result.cards == ()


@pytest.mark.asyncio
async def test_orchestrator_dedupes_identical_cards() -> None:
    handler = _Handler(
        ToolResult(
            request_id="r",
            tool_name="search_listings",
            success=True,
            data={"items": [{"id": "L1", "title": "Drevo"}]},
        )
    )
    orch = _orch(_Gateway([("search_listings", "{}"), ("search_listings", "{}")]), handler)

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert len(result.cards) == 1  # same (type, id) collapsed


@pytest.mark.asyncio
async def test_orchestrator_survives_broken_card_builder() -> None:
    def boom(_tool: str, _data: object) -> list[dict]:
        raise RuntimeError("builder exploded")

    from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
        ActorToolPermissionEngine,
    )
    from app.modules.agent_platform.infrastructure.policy.allowlist_policy_engine import (
        AllowlistPolicyEngine,
    )

    handler = _Handler(
        ToolResult(request_id="r", tool_name="search_listings", success=True, data={"items": []})
    )
    orch = AgentOrchestrator(
        gateway=_Gateway([("search_listings", "{}")]),
        tool_schemas=(),
        tool_handlers={"search_listings": handler},
        model="test",
        policy=AllowlistPolicyEngine(allowed_tool_names=frozenset({"search_listings"})),
        permission=ActorToolPermissionEngine(
            allowed_actor_types=frozenset({"user"}),
            allowed_scopes=frozenset({("listings", "search")}),
        ),
        tool_scopes={"search_listings": ("listings", "search")},
        card_builder=boom,
    )

    result = await orch.respond(system_prompt="s", user_message="u", actor_id="a1")

    assert result.text == "Hotovo."
    assert result.cards == ()


def test_total_card_cap_is_sane() -> None:
    assert MAX_TOTAL_CARDS >= MAX_CARDS
