"""OpenAI-compatible tool schemas for Groq function calling."""

from __future__ import annotations

from typing import Any

COMPANY_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_companies",
        "description": (
            "Vyhľadá firmy v CMEP podľa kritérií (materiál, lokalita, rola). "
            "Použi vždy keď sa používateľ pýta na firmy, odberateľov, dodávateľov."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Fulltextové hľadanie (názov, materiál, mesto).",
                },
                "company_type": {
                    "type": "string",
                    "description": "Typ firmy (napr. sro, as, zivnost).",
                },
                "seller_capability": {
                    "type": "boolean",
                    "description": "Firma vie predávať (ponúka materiál).",
                },
                "buyer_capability": {
                    "type": "boolean",
                    "description": "Firma vie nakupovať (hľadá materiál).",
                },
                "logistics_capability": {
                    "type": "boolean",
                    "description": "Firma má logistiku / dopravu.",
                },
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                },
            },
        },
    },
}


LISTING_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_listings",
        "description": (
            "Vyhľadá ponuky materiálov na marketplace. "
            "Použi keď sa používateľ pýta na konkrétne ponuky, materiály, dostupnosť."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Fulltextové hľadanie (názov, materiál).",
                },
                "material_type": {
                    "type": "string",
                    "description": "Typ materiálu (wood, metal, paper, plastics, bio).",
                },
                "location": {
                    "type": "string",
                    "description": "Lokalita (mesto, región).",
                },
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                },
            },
        },
    },
}


def build_default_tools() -> tuple[dict[str, Any], ...]:
    return (COMPANY_SEARCH_SCHEMA, LISTING_SEARCH_SCHEMA)


ADMIN_PLATFORM_STATS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_platform_stats",
        "description": (
            "READ-ONLY admin tool. Vráti počty entít: companies, listings, users, "
            "inquiries, documents, ai_conversations, ai_messages. "
            "Použi keď sa architekt pýta na štatistiky platformy."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

ADMIN_RECENT_ACTIVITY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_recent_activity",
        "description": (
            "READ-ONLY admin tool. Vráti posledné udalosti z activity_events. "
            "Použi keď sa architekt pýta čo sa dialo na platforme."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "minimum": 1, "maximum": 30, "default": 7},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
            },
        },
    },
}

ADMIN_COMPANIES_TIERS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_companies_with_tiers",
        "description": (
            "READ-ONLY admin tool. Vráti zoznam firiem s ich subscription_tier "
            "(free/pro/ai). Voliteľne filtruj podľa konkrétneho tieru."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tier": {"type": "string", "enum": ["free", "pro", "ai"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
        },
    },
}

ADMIN_MY_CONTEXT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_my_company_context",
        "description": (
            "READ-ONLY admin tool. Vráti základný kontext firmy (názov, mesto, tier, "
            "capabilities). Použi keď architekt potrebuje rýchly prehľad."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


def build_admin_tools() -> tuple[dict[str, Any], ...]:
    """Return admin-only tool schemas.

    These are attached to the LLM only when the caller is a platform admin.
    """
    return (
        ADMIN_PLATFORM_STATS_SCHEMA,
        ADMIN_RECENT_ACTIVITY_SCHEMA,
        ADMIN_COMPANIES_TIERS_SCHEMA,
        ADMIN_MY_CONTEXT_SCHEMA,
    )
