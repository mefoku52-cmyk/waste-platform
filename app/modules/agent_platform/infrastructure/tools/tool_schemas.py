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


NEARBY_COMPANIES_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_nearby_companies",
        "description": (
            "READ-ONLY. Vyhľadá firmy v okolí podľa mesta/regiónu. "
            "Použi keď sa používateľ pýta na firmy v okolí, odberateľov v regióne, "
            "alebo kto kupuje materiál v jeho okolí."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "near": {"type": "string", "description": "Mesto alebo región."},
                "buyer_capability": {"type": "boolean"},
                "seller_capability": {"type": "boolean"},
                "material_type": {
                    "type": "string",
                    "description": "Materiál (wood, metal, paper, plastics, bio, alebo voľný text).",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
            },
            "required": ["near"],
        },
    },
}


LISTING_TRANSPORT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_listing_transport",
        "description": (
            "READ-ONLY. Vypočíta trasu, vzdialenosť, čas a náklady na prepravu "
            "k ponuke. Použi keď sa používateľ pýta na dopravu, vzdialenosť, "
            "cestu alebo cenu prepravy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "UUID ponuky."},
                "from_location": {"type": "string", "description": "Odkiaľ (mesto)."},
                "consumption": {"type": "number", "default": 28.0},
                "fuel_price": {"type": "number", "default": 1.49},
                "roundtrip": {"type": "boolean", "default": False},
            },
            "required": ["from_location"],
        },
    },
}


def build_transport_tools() -> tuple[dict[str, Any], ...]:
    """Transport + nearby tools. Available to every authenticated user."""
    return (NEARBY_COMPANIES_SCHEMA, LISTING_TRANSPORT_SCHEMA)


# ─── CLIENT-SIDE ACTIONS (Comet-style) ─────────────────────
# Tieto tooly sa nevykonávajú na serveri. Orchestrátor ich vráti
# vo `tool_calls`, frontend ich aplikuje na aktuálnu stránku.

FILL_FORM_FIELD_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "fill_form_field",
        "description": (
            "Vyplní jedno pole vo formulári, ktorý používateľ práve vidí. "
            "Použi keď vieš hodnotu, ktorá patrí do formulára ponuky "
            "(title, materialType, quantity, unit, price, currency, condition, "
            "location, description) alebo formulára firmy "
            "(legalName, tradingName, registrationNumber, city, postalCode, "
            "countryCode, email, phone, addressLine1, entityType, companyType). "
            "Volaj toľkokrát, koľko polí chceš vyplniť. Po každom volaní povedz "
            "používateľovi krátko ČO si vyplnil."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "Názov poľa (musí byť jedno z polí aktuálneho formulára).",
                },
                "value": {
                    "description": "Hodnota poľa (string, number, boolean).",
                },
            },
            "required": ["field", "value"],
        },
    },
}


NAVIGATE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "navigate",
        "description": (
            "Presmeruje používateľa na inú stránku CMEP. Použi iba keď "
            "používateľ výslovne chce niekam ísť, alebo keď mu chceš niečo ukázať."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Relatívna cesta v rámci CMEP, napr. '/dashboard/listings/new'.",
                },
            },
            "required": ["url"],
        },
    },
}


HIGHLIGHT_FIELD_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "highlight_field",
        "description": (
            "Zvýrazní pole vo formulári na 1 sekundu (zelený rámik). "
            "Použi keď chceš používateľovi ukázať, ktoré pole má vyplniť ručne."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
            },
            "required": ["field"],
        },
    },
}


SHOW_TOAST_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "show_toast",
        "description": (
            "Zobrazí krátky toast (oznam) v rohu obrazovky. "
            "Použi na potvrdenie akcie alebo upozornenie."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "level": {"type": "string", "enum": ["info", "success", "warning", "error"]},
            },
            "required": ["message"],
        },
    },
}


# ─── USER READ TOOLS (identity-bound, safe) ─────────────────

GET_MY_LISTINGS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_my_listings",
        "description": (
            "READ-ONLY. Vráti PONUKY aktuálneho používateľa (jeho firiem). "
            "Použi keď sa používateľ pýta 'koľko mám ponúk', 'moje ponuky', "
            "'čo predávam', 'moje drafty'. Nikdy nevracia cudzie ponuky."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["draft", "published", "reserved", "sold", "archived"],
                    "description": "Voliteľný filter podľa stavu.",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
            },
        },
    },
}


GET_MY_COMPANY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_my_company",
        "description": (
            "READ-ONLY. Vráti základné údaje o firme aktuálneho používateľa "
            "(názov, mesto, status, tier). "
            "Použi keď sa používateľ pýta na svoju firmu alebo jej stav."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


GET_LISTING_DETAILS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_listing_details",
        "description": (
            "READ-ONLY. Vráti detail jednej ponuky podľa listing_id. "
            "Používateľ musí mať oprávnenie (jeho firma alebo admin). "
            "Použi keď sa pýta na konkrétnu ponuku."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "UUID ponuky."},
            },
            "required": ["listing_id"],
        },
    },
}


GET_LISTING_STATS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_listing_stats",
        "description": (
            "READ-ONLY. Vráti štatistiky ponuky (počet zobrazení, unikátni "
            "návštevníci). Iba vlastník ponuky smie vidieť. "
            "Použi keď sa používateľ pýta 'koľko views', 'koľkokrát si to videli'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "UUID ponuky."},
            },
            "required": ["listing_id"],
        },
    },
}


GET_COMPANY_LISTINGS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_company_listings",
        "description": (
            "READ-ONLY. Vráti verejné (published) ponuky firmy. "
            "Použi keď sa používateľ pýta na ponuky konkrétnej firmy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "UUID firmy."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
            },
            "required": ["company_id"],
        },
    },
}


GET_RECOMMENDATIONS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_recommendations",
        "description": (
            "READ-ONLY. Vráti existujúce odporúčania pre ponuku "
            "(kupujúci, prepravcovia, skóre). "
            "Použi keď sa používateľ pýta 'kto by to kúpil', 'komu to odporučiť'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "UUID ponuky."},
            },
            "required": ["listing_id"],
        },
    },
}


def build_user_read_tools() -> tuple[dict[str, Any], ...]:
    """Identity-bound READ tools. Available to every authenticated user."""
    return (
        GET_MY_LISTINGS_SCHEMA,
        GET_MY_COMPANY_SCHEMA,
        GET_LISTING_DETAILS_SCHEMA,
        GET_LISTING_STATS_SCHEMA,
        GET_COMPANY_LISTINGS_SCHEMA,
        GET_RECOMMENDATIONS_SCHEMA,
    )


# ─── NAVIGATION CLIENT TOOLS ────────────────────────────────

OPEN_LISTING_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_listing",
        "description": (
            "Otvorí detail ponuky v UI. Použi keď chceš používateľovi ukázať konkrétnu ponuku."
        ),
        "parameters": {
            "type": "object",
            "properties": {"listing_id": {"type": "string"}},
            "required": ["listing_id"],
        },
    },
}

OPEN_COMPANY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_company",
        "description": "Otvorí profil firmy v UI.",
        "parameters": {
            "type": "object",
            "properties": {"company_id": {"type": "string"}},
            "required": ["company_id"],
        },
    },
}

OPEN_NEW_LISTING_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_new_listing",
        "description": (
            "Otvorí formulár novej ponuky. Použi keď chce používateľ "
            "pridať novú ponuku. Po otvorení môžeš pokračovať fill_form_field."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_LISTINGS_LIST_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_listings_list",
        "description": "Otvorí zoznam ponúk.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_COMPANIES_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_companies",
        "description": "Otvorí zoznam firiem.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_DASHBOARD_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_dashboard",
        "description": "Otvorí hlavný dashboard.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_INQUIRIES_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_inquiries",
        "description": "Otvorí zoznam dopytov používateľa.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_NEW_COMPANY_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_new_company",
        "description": (
            "Otvorí formulár pre pridanie novej firmy. Použi keď chce "
            "používateľ zaregistrovať novú firmu. Po otvorení môžeš pokračovať "
            "fill_form_field."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_DOCUMENTS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_documents",
        "description": "Otvorí zoznam dokumentov používateľa.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_NEW_DOCUMENT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_new_document",
        "description": (
            "Otvorí formulár pre nahratie nového dokumentu. Použi keď chce "
            "používateľ pridať dokument."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_CHAT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_chat",
        "description": "Otvorí interný chat (správy) platformy.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_SETTINGS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_settings",
        "description": "Otvorí nastavenia účtu (zabezpečenie, heslo).",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_TRANSPORT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_transport",
        "description": "Otvorí stránku prepravcov.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_SUBSCRIPTION_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_subscription",
        "description": "Otvorí stránku predplatného.",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_MARKETPLACE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_marketplace",
        "description": "Otvorí marketplace (všetky ponuky).",
        "parameters": {"type": "object", "properties": {}},
    },
}

OPEN_ADMIN_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "open_admin",
        "description": ("Otvorí administráciu platformy. Dostupné iba pre administrátora."),
        "parameters": {"type": "object", "properties": {}},
    },
}


# ─── CLIENT ACTION AGGREGATION (musí byť na konci — reference na všetky) ─
CLIENT_ACTION_SCHEMAS: tuple[dict[str, Any], ...] = (
    FILL_FORM_FIELD_SCHEMA,
    NAVIGATE_SCHEMA,
    HIGHLIGHT_FIELD_SCHEMA,
    SHOW_TOAST_SCHEMA,
    OPEN_LISTING_SCHEMA,
    OPEN_COMPANY_SCHEMA,
    OPEN_NEW_LISTING_SCHEMA,
    OPEN_LISTINGS_LIST_SCHEMA,
    OPEN_COMPANIES_SCHEMA,
    OPEN_DASHBOARD_SCHEMA,
    OPEN_INQUIRIES_SCHEMA,
    OPEN_NEW_COMPANY_SCHEMA,
    OPEN_DOCUMENTS_SCHEMA,
    OPEN_NEW_DOCUMENT_SCHEMA,
    OPEN_CHAT_SCHEMA,
    OPEN_SETTINGS_SCHEMA,
    OPEN_TRANSPORT_SCHEMA,
    OPEN_SUBSCRIPTION_SCHEMA,
    OPEN_MARKETPLACE_SCHEMA,
)

# Attached to the model ONLY when the caller is a platform admin.
ADMIN_CLIENT_ACTION_SCHEMAS: tuple[dict[str, Any], ...] = (OPEN_ADMIN_SCHEMA,)


CLIENT_ACTION_NAMES: frozenset[str] = frozenset(
    s["function"]["name"] for s in CLIENT_ACTION_SCHEMAS + ADMIN_CLIENT_ACTION_SCHEMAS
)

OPENLIST_LIST_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "external.openlist.list",
        "description": (
            "READ-ONLY. Zoznam súborov a adresárov cez OpenList. "
            "Použi iba na kontrolu dostupných projektových súborov. "
            "Nikdy nepoužíva write, delete, move ani upload operácie."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relatívna cesta v povolenom OpenList root-e. "
                        "Použi napr. '.' alebo 'app/modules'."
                    ),
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 50,
                },
            },
            "required": ["path"],
        },
    },
}

OPENLIST_GET_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "external.openlist.get",
        "description": (
            "READ-ONLY. Načíta metadata alebo obsah súboru cez OpenList. "
            "Použi iba na kontrolu projektových súborov. "
            "Nikdy neupravuje ani nemaže súbory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relatívna cesta v povolenom OpenList root-e. "
                        "Nesmie obsahovať '..', absolútnu cestu ani backslash."
                    ),
                },
            },
            "required": ["path"],
        },
    },
}

OPENLIST_READONLY_SCHEMAS: tuple[dict[str, Any], ...] = (
    OPENLIST_LIST_SCHEMA,
    OPENLIST_GET_SCHEMA,
)

OPENLIST_READONLY_NAMES: frozenset[str] = frozenset(
    s["function"]["name"] for s in OPENLIST_READONLY_SCHEMAS
)


# ─── PROJECT READ TOOLS (direct Python file read, bez OpenList) ─

PROJECT_READ_FILE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "project_read_file",
        "description": (
            "READ-ONLY. Prečíta textový súbor z repozitára waste-platform. "
            "Obmedzenia: iba ~/waste-platform, max 1 MB, žiadne súbory mimo repa. "
            "Write/delete/move nie sú podporované."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relatívna cesta, napr. 'app/main.py'."},
            },
            "required": ["path"],
        },
    },
}


PROJECT_LIST_DIR_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "project_list_dir",
        "description": "READ-ONLY. Vypíše obsah adresára v repozitári. Skryje .git, __pycache__, node_modules, .next, venv.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relatívna cesta. Prázdny = koreň."},
            },
            "required": ["path"],
        },
    },
}


def build_project_read_tools() -> tuple[dict[str, Any], ...]:
    """READ-ONLY project file access (direct Python, nie OpenList)."""
    return (PROJECT_READ_FILE_SCHEMA, PROJECT_LIST_DIR_SCHEMA)
