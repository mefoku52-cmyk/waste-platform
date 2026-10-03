"""Public directory email lookup.

Fallback sources:
1. Zlaté stránky

Only public pages are used.
An email is accepted only when it belongs to the matched company card.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.modules.lead_finder.application.services.email_finder import (
    _FREE_EMAIL_DOMAINS,
)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

_JUNK_EMAIL_MARKERS = (
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "example.com",
    "example.org",
    "example.net",
)

_LEGAL_SUFFIXES = (
    "s.r.o.",
    "s. r. o.",
    "s.r.o",
    "s. r. o",
    "a.s.",
    "a. s.",
    "a.s",
    "a. s",
    "k.s.",
    "k. s.",
    "k.s",
    "k. s",
    "spol. s r.o.",
    "spol. s r. o.",
    "spol s r.o.",
    "spol s r o",
)

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Safari/537.36"),
    "Accept": "text/html",
}

# Domains that are never a company's own homepage: business registers and
# directory cross-links. website_finder keeps its own (broader) skip list;
# this one only guards _extract_card_website, which previously returned the
# first external link on the card (often an indexpodnikatela.sk register URL).
_NON_COMPANY_WEBSITE_DOMAINS = (
    "zlatestranky.sk",
    "indexpodnikatela.sk",
)


def _ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _normalize_name(text: str) -> str:
    text = _ascii(text).lower()

    for suffix in _LEGAL_SUFFIXES:
        text = text.replace(suffix, " ")

    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _name_tokens(text: str) -> list[str]:
    normalized = _normalize_name(text)

    return [token for token in normalized.split() if len(token) >= 3]


def _names_match(target: str, card_name: str) -> bool:
    """Require the meaningful target name to match the directory card."""
    target_normalized = _normalize_name(target)
    card_normalized = _normalize_name(card_name)

    if not target_normalized or not card_normalized:
        return False

    # Strongest case: normalized names are identical.
    if target_normalized == card_normalized:
        return True

    target_tokens = _name_tokens(target)
    card_tokens = set(_name_tokens(card_name))

    if not target_tokens:
        return False

    # A single short/common token is not enough.
    if len(target_tokens) == 1:
        token = target_tokens[0]
        return len(token) >= 6 and token in card_tokens

    # Every meaningful target token must occur in the card name.
    return all(token in card_tokens for token in target_tokens)


def _extract_ico(card) -> str | None:
    for link in card.select('a[href*="indexpodnikatela.sk"]'):
        href = link.get("href", "")

        match = re.search(r"(\d{8})(?:/)?$", href.rstrip("/"))
        if match:
            return match.group(1)

        match = re.search(r"/(\d{8})(?:[/?#]|$)", href)
        if match:
            return match.group(1)

    return None


def _extract_card_name(card) -> str | None:
    # Zlaté stránky firm profiles use /firmy/{city}/{H|T}{id}/...
    profile_pattern = re.compile(r"/firmy/[^/]+/[HT]\d+/")

    for link in card.select('a[href*="/firmy/"]'):
        href = link.get("href", "")

        if profile_pattern.search(href):
            title = link.get_text(" ", strip=True)
            if title:
                return title

    return None


def _extract_card_email(card) -> str | None:
    for anchor in card.select('a[href^="mailto:"]'):
        href = anchor.get("href", "")

        email = href.removeprefix("mailto:").split("?", 1)[0].strip().lower()

        if not _EMAIL_RE.fullmatch(email):
            continue

        domain = email.rsplit("@", 1)[-1]

        if domain in _FREE_EMAIL_DOMAINS:
            # Consumer/telco mailboxes (Gmail, mail.t-com.sk, …) are not
            # valid B2B company contacts; skip this mailto anchor.
            continue

        if any(marker in email for marker in _JUNK_EMAIL_MARKERS):
            continue

        return email

    return None


def _is_non_company_website(href: str) -> bool:
    """Reject register/directory cross-links that are not a company homepage."""
    try:
        domain = urlparse(href).netloc.lower().split(":")[0]
    except Exception:
        return True

    if not domain:
        return True

    return any(
        domain == blocked or domain.endswith("." + blocked)
        for blocked in _NON_COMPANY_WEBSITE_DOMAINS
    )


def _extract_card_website(card) -> str | None:
    """Return the company's own homepage URL from a directory card.

    Uses the dedicated ``li.link`` slot rather than the first external anchor:
    cards without a homepage still link to indexpodnikatela.sk (business
    register), which is NOT the company website. Microdata
    ``span[itemprop="url"]`` is used as a fallback because it survives CSS
    class renames.
    """
    for anchor in card.select('li.link a[href^="http"]'):
        href = str(anchor.get("href") or "").strip()

        if _is_non_company_website(href):
            continue

        return href

    for span in card.select('span[itemprop="url"]'):
        href = str(span.get("content") or span.get_text(" ", strip=True) or "").strip()

        if not href.startswith(("http://", "https://")):
            continue

        if _is_non_company_website(href):
            continue

        return href

    return None


def _extract_joomla_cloak_email(html: str) -> str | None:
    """Decode Joomla email-cloak JavaScript from a public company page."""
    if not html:
        return None

    import html as html_module

    def valid_email(value: str) -> str | None:
        candidate = html_module.unescape(value).strip().lower()

        if not _EMAIL_RE.fullmatch(candidate):
            return None

        if any(marker in candidate for marker in _JUNK_EMAIL_MARKERS):
            return None

        return candidate

    # Joomla cloak assignments contain quoted JavaScript strings with HTML
    # entities such as '&#111;'. The semicolon inside the HTML entity is NOT
    # the end of the JavaScript assignment, so the parser must understand
    # quoted literals instead of splitting on every semicolon.
    token = r"(?:'[^']*'|addy[A-Za-z0-9_]*)"

    assignment_re = re.compile(
        rf"\b(?:var\s+)?"
        rf"(addy[A-Za-z0-9_]*)"
        rf"\s*=\s*"
        rf"({token}(?:\s*\+\s*{token})*)"
        rf"\s*;",
        re.DOTALL,
    )

    values: dict[str, str] = {}

    for match in assignment_re.finditer(html):
        name = match.group(1)
        expression = match.group(2)

        parts = re.split(r"\s*\+\s*", expression)
        result: list[str] = []

        for part in parts:
            part = part.strip()

            literal = re.fullmatch(r"'([^']*)'", part)
            if literal:
                result.append(html_module.unescape(literal.group(1)))
                continue

            variable = re.fullmatch(r"addy[A-Za-z0-9_]*", part)
            if variable:
                previous = values.get(variable.group(0))
                if previous is None:
                    result = []
                    break

                result.append(previous)
                continue

            result = []
            break

        if not result:
            continue

        value = "".join(result)
        values[name] = value

        email = valid_email(value)
        if email:
            return email

    return None


def _card_matches(
    card,
    company_name: str,
    ico: str | None,
) -> bool:
    card_name = _extract_card_name(card)

    if not card_name:
        return False

    # IČO is the strongest available identifier.
    if ico:
        card_ico = _extract_ico(card)

        if card_ico and card_ico == re.sub(r"\D", "", ico):
            return True

    return _names_match(company_name, card_name)


def _match_card(
    html: str,
    company_name: str,
    ico: str | None = None,
):
    """Return the first directory card matching the company, else None."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    for card in soup.select("div.profile-holder"):
        if _card_matches(card, company_name, ico):
            return card

    return None


def _pick(
    html: str,
    company_name: str,
    ico: str | None = None,
) -> str | None:
    """Return the email published directly on a matching company card.

    Only the card's own ``mailto:`` link is used here -- no extra HTTP.

    Homepage extraction lives in ``website_contact_crawler``, which is the
    single component allowed to fetch company websites. Keeping this
    function HTTP-free means the "crawl the homepage" decision is made in
    exactly one place.
    """
    card = _match_card(html, company_name, ico)

    if card is None:
        return None

    return _extract_card_email(card)


def _get(url: str) -> str:
    try:
        response = httpx.get(
            url,
            headers=_HEADERS,
            timeout=12.0,
            follow_redirects=True,
        )
    except Exception:
        return ""

    if response.status_code != 200:
        return ""

    return response.text


def _search_queries(company_name: str) -> list[str]:
    """Build safe search terms for Zlaté stránky."""
    normalized = _normalize_name(company_name)

    if not normalized:
        return []

    queries: list[str] = []

    # Full normalized company name.
    queries.append(normalized)

    tokens = _name_tokens(company_name)

    # Also search the first two meaningful terms.
    # This helps when the directory rejects an exact legal-name query.
    if len(tokens) >= 2:
        queries.append(" ".join(tokens[:2]))

    # For longer names also try the first distinctive token.
    if len(tokens) >= 3 and len(tokens[0]) >= 5:
        queries.append(tokens[0])

    result: list[str] = []

    for query in queries:
        if query and query not in result:
            result.append(query)

    return result


def lookup_public_email(
    company_name: str,
    city: str | None = None,
    ico: str | None = None,
) -> str | None:
    """Find a company-related public email via Zlaté stránky.

    Two stages:
    1. the email published directly on the matched directory card, then
    2. the company homepage linked from that card, crawled by
       ``website_contact_crawler``.
    """
    if not company_name or not company_name.strip():
        return None

    queries = _search_queries(company_name)

    if not queries:
        return None

    # City is currently not injected into the query because the directory
    # already returns city-specific profile URLs. It remains part of the API
    # for future stricter card validation.
    _ = city

    # Lazy import on purpose: website_contact_crawler imports helpers from
    # this module (_extract_joomla_cloak_email, _normalize_name,
    # _JUNK_EMAIL_MARKERS, _EMAIL_RE). A module-level import would create a
    # circular import.
    from app.modules.lead_finder.application.services.website_contact_crawler import (
        crawl_contact_email,
    )

    for query in queries:
        url = "https://www.zlatestranky.sk/Search?what=" + quote(query, safe="")

        html = _get(url)

        email = _pick(
            html,
            company_name=company_name,
            ico=ico,
        )

        if email:
            return email

        card = _match_card(html, company_name=company_name, ico=ico)

        if card is None:
            continue

        homepage_url = _extract_card_website(card)

        if not homepage_url:
            return None

        email, _source_url = crawl_contact_email(homepage_url, company_name)

        if email:
            return email

        return None

    return None
