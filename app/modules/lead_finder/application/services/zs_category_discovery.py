"""Category-based discovery from Zlaté stránky.

Instead of searching the directory per company (a lookup that mostly
misses), crawl whole categories and read contacts straight off each card.

This is the only discovery path that works from a datacenter IP: plain
httpx + BeautifulSoup, no search engine, no per-company lookup, and the
email is taken directly from the card so nothing is ever invented.

GDPR: every company keeps ``source_url`` — the exact public page the data
was read from — so provenance is auditable.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup

from app.modules.lead_finder.application.services.directory_lookup import (
    _extract_card_email,
    _extract_card_name,
    _extract_card_website,
    _get,
)

logger = logging.getLogger(__name__)

# Hardcoded category slugs from the directory's own category tree. Kept
# explicit rather than crawled so a run is reproducible.
CATEGORY_SLUGS: tuple[str, ...] = (
    "odpad",
    "odpady",
    "Recyklácia",
    "Ekologické zariadenia a služby",
    "kovový odpad",
    "zberné suroviny",
    "druhotné suroviny",
    "drevospracovanie",
    "plasty",
    "kompost",
    "kontajnery",
    "likvidácia odpadu",
    "doprava odpadu",
    "sklo",
    "papier",
    "kovošrot",
    "zberný dvor",
    "zberne",
    "odvoz odpadu",
    "nebezpečný odpad",
    "stavebný odpad",
    "železo",
    "hliník",
)


@dataclass(frozen=True)
class DiscoveredCompany:
    """One company as published on a public directory card."""

    company_name: str
    email: str
    phone: str | None = None
    website: str | None = None
    city: str | None = None
    source_url: str = ""


_BASE_URL = "https://www.zlatestranky.sk"

# Card profile links look like /firmy/{city}/{H|T}{id}/{slug}/
_PROFILE_LINK_RE = re.compile(r"/firmy/([^/]+)/[HT]\d+/")


def _category_url(category_slug: str, page: int) -> str:
    """Build the category listing URL for one page."""
    return f"{_BASE_URL}/firmy/-/q_{quote(category_slug, safe='')}/{page}/"


def _extract_card_phone(card) -> str | None:
    for anchor in card.select('a[href^="tel:"]'):
        value = str(anchor.get("href") or "").removeprefix("tel:").strip()

        if value:
            return value

    return None


def _extract_card_location(card) -> tuple[str | None, str | None]:
    """Return ``(city, profile_url)`` from the card's profile link.

    The directory encodes the city as the first path segment, so no extra
    selector is needed. ``profile_url`` is the company's own public record
    and doubles as the GDPR ``source_url``.
    """
    for link in card.select('a[href*="/firmy/"]'):
        href = str(link.get("href") or "").strip()

        match = _PROFILE_LINK_RE.search(href)

        if not match:
            continue

        city = unquote(match.group(1).replace("+", " ")).strip() or None

        profile_url = href if href.startswith("http") else _BASE_URL + href

        return city, profile_url

    return None, None


def _extract_card_data(card) -> DiscoveredCompany | None:
    """Read one card into a company record.

    Returns ``None`` when the card carries no usable email or no name —
    a company without a directly published email is not a lead.

    The name is read *before* the email on purpose: the D2 rule needs it to
    decide whether a free-provider address (Gmail, Zoznam, …) actually
    belongs to the company.
    """
    company_name = _extract_card_name(card)

    if not company_name:
        return None

    email = _extract_card_email(card, company_name)

    if not email:
        return None

    city, profile_url = _extract_card_location(card)

    return DiscoveredCompany(
        company_name=company_name,
        email=email,
        phone=_extract_card_phone(card),
        website=_extract_card_website(card),
        city=city,
        source_url=profile_url or "",
    )


def _iter_pages(
    category_slug: str,
    max_pages: int = 20,
    start_page: int = 1,
) -> Iterator[list]:
    """Yield the cards of each category page, stopping when none remain.

    Beyond the last page the directory answers HTTP 400, which ``_get``
    turns into an empty string — so an empty response and an empty card
    list both end the iteration.

    Pages are fetched with a 1s pause between requests to stay polite.
    """
    for page in range(start_page, max_pages + 1):
        if page > start_page:
            time.sleep(1.0)

        url = _category_url(category_slug, page)

        html = _get(url)

        if not html:
            logger.debug("Category page unreachable/empty, stopping: %s", url)
            return

        cards = BeautifulSoup(html, "html.parser").select("div.profile-holder")

        if not cards:
            logger.debug("No cards on page %s, stopping", url)
            return

        yield cards


def discover_from_category(
    category_slug: str,
    page: int = 1,
    max_pages: int = 20,
) -> list[DiscoveredCompany]:
    """Return every unique company published under one directory category.

    ``page`` is the first page to read; paging continues until the directory
    runs out of cards or ``max_pages`` is reached.

    Companies are deduplicated by lower-cased email, because the same firm
    is listed under several related categories (``odpad`` and ``odpady``).

    The email comes straight from the card — no lookup, no search engine,
    no guessing. Nothing is ever constructed.
    """
    if not category_slug or not category_slug.strip():
        return []

    if page < 1:
        page = 1

    seen: set[str] = set()
    found: list[DiscoveredCompany] = []

    for cards in _iter_pages(category_slug, max_pages=max_pages, start_page=page):
        for card in cards:
            company = _extract_card_data(card)

            if company is None:
                continue

            key = company.email.lower()

            if key in seen:
                continue

            seen.add(key)
            found.append(company)

    logger.info(
        "Category discovery: slug=%r pages<=%s unique=%d",
        category_slug,
        max_pages,
        len(found),
    )

    return found


__all__ = ["CATEGORY_SLUGS", "DiscoveredCompany", "discover_from_category"]
