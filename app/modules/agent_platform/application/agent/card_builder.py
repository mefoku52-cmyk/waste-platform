"""Build UI cards from successful server-tool results.

A *card* is a small, safe, JSON-serialisable dict the frontend renders as a
rich result next to the assistant text (listing / company / stats). Design
rules, kept deliberately strict:

* Cards are only built from data a tool already returned to the *current*
  caller — the card builder never queries anything and never widens access.
* Every link is an INTERNAL dashboard route derived from a whitelisted entity
  type + a validated id. Raw/URL-ish values from the model or DB never reach
  the ``href`` field.
* Output is capped so a single turn cannot flood the UI.

The builder is pure and synchronous; it is wired into the orchestrator as a
callback (same pattern as the audit / client-action validator callbacks).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

MAX_CARDS = 12

# Same conservative shape the client-action validator uses for ids.
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# Listing-detail / company-detail dashboard routes (verified against
# apps/web/src/app/dashboard/**). A card href is only ever one of these.
_LISTING_ROUTE = "/dashboard/listings/{id}"
_COMPANY_ROUTE = "/dashboard/companies/{id}"


def _safe_id(value: Any) -> str | None:
    """Return a validated id string, or None if it is missing/unsafe."""
    text = str(value or "").strip()
    if text and _SAFE_ID_RE.match(text):
        return text
    return None


def _text(value: Any) -> str:
    """Coerce a value to a short, safe display string."""
    if value is None:
        return ""
    text = str(value).strip()
    return text[:200]


def _label(value: Any) -> str | None:
    """Human-readable label from an enum-or-string value."""
    if value is None:
        return None
    text = str(getattr(value, "value", value)).strip()
    return text or None


def _join_meta(*parts: str | None) -> str:
    return " · ".join(p for p in parts if p)


def _listing_card(item: Mapping[str, Any]) -> dict[str, Any] | None:
    lid = _safe_id(item.get("id"))
    if not lid:
        return None
    # search_listings uses snake_case, the user tools use camelCase.
    material = item.get("materialType") or item.get("material_type")
    quantity = item.get("quantity")
    unit = item.get("unit")
    location = item.get("location")
    price = item.get("price")
    currency = item.get("currency")

    amount = None
    if quantity is not None and str(quantity).strip():
        amount = f"{_text(quantity)} {_text(unit)}".strip()

    price_label = None
    if price is not None and str(price).strip():
        price_label = f"{_text(price)} {_text(currency)}".strip()

    subtitle = _join_meta(
        _label(material),
        _text(location) or None,
        amount or None,
        price_label or None,
    )
    return {
        "type": "listing",
        "id": lid,
        "title": _text(item.get("title")) or "Ponuka",
        "subtitle": subtitle,
        "image": _text(item.get("imageUrl") or item.get("image_url")) or None,
        "status": _label(item.get("status")),
        "href": _LISTING_ROUTE.format(id=lid),
    }


def _company_card(item: Mapping[str, Any]) -> dict[str, Any] | None:
    cid = _safe_id(item.get("id"))
    if not cid:
        return None
    name = (
        _text(item.get("trading_name"))
        or _text(item.get("tradingName"))
        or _text(item.get("legal_name"))
        or _text(item.get("legalName"))
        or "Firma"
    )
    subtitle = _join_meta(
        _text(item.get("city")) or None,
        _text(item.get("country_code") or item.get("countryCode")) or None,
        _label(item.get("company_type") or item.get("companyType")),
    )
    return {
        "type": "company",
        "id": cid,
        "title": name,
        "subtitle": subtitle,
        "image": _text(item.get("logoUrl") or item.get("logo_url")) or None,
        "status": _label(item.get("status")),
        "href": _COMPANY_ROUTE.format(id=cid),
    }


def _stats_card(data: Mapping[str, Any]) -> dict[str, Any] | None:
    stats = data.get("stats")
    if not isinstance(stats, Mapping) or not stats:
        return None
    meta = [
        {"label": _text(key), "value": _text(val) if val is not None else "—"}
        for key, val in stats.items()
    ]
    return {
        "type": "stats",
        "id": None,
        "title": "Štatistiky platformy",
        "subtitle": "",
        "image": None,
        "status": None,
        "href": None,
        "meta": meta,
    }


def _items_from(data: Any) -> list[Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, Mapping)]


def build_cards(tool_name: str, data: Any) -> list[dict[str, Any]]:
    """Map one successful tool result to zero or more UI cards.

    Unknown tools / shapes yield an empty list — never an error.
    """
    cards: list[dict[str, Any]] = []

    if tool_name in {"search_listings", "get_my_listings", "get_company_listings"}:
        for item in _items_from(data):
            card = _listing_card(item)
            if card:
                cards.append(card)

    elif tool_name in {"search_companies", "search_nearby_companies"}:
        for item in _items_from(data):
            card = _company_card(item)
            if card:
                cards.append(card)

    elif tool_name == "get_listing_details" and isinstance(data, Mapping):
        listing = data.get("listing")
        if isinstance(listing, Mapping):
            card = _listing_card(listing)
            if card:
                cards.append(card)

    elif tool_name == "get_my_company" and isinstance(data, Mapping):
        company = data.get("company")
        if isinstance(company, Mapping):
            card = _company_card(company)
            if card:
                cards.append(card)

    elif tool_name == "get_platform_stats" and isinstance(data, Mapping):
        card = _stats_card(data)
        if card:
            cards.append(card)

    return cards[:MAX_CARDS]
