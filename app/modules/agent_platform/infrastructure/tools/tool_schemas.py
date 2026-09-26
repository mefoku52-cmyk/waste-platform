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
