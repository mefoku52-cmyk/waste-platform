"""Public email lookup via Google Search (no API key)."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

_JUNK_EMAIL_MARKERS = (
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "example.com",
    "example.org",
    "example.net",
)

_SKIP_DOMAINS = (
    "obchodnyvestnik",
    "orsr.sk",
    "finstat.sk",
    "zlatestranky.sk",
    "indexpodnikatela.sk",
    "registeruz.sk",
    "firmy.sk",
    "firmydata.sk",
    "valida.sk",
    "peniaze.sk",
    "podnikajte.sk",
    "bazos.sk",
    "heureka.sk",
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8",
}


def _ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _is_junk(email: str) -> bool:
    e = email.lower()
    return any(m in e for m in _JUNK_EMAIL_MARKERS)


def _email_acceptable(email: str, company_name: str | None = None) -> bool:
    if _is_junk(email):
        return False
    local, _, domain = email.partition("@")
    domain = domain.lower()
    if domain in _CONSUMER_EMAIL_DOMAINS:
        if not company_name:
            return False
        norm_company = _normalize_for_match(company_name)
        norm_local = _normalize_for_match(local)
        ok = False
        for i in range(len(norm_company) - 2):
            chunk = norm_company[i : i + 3]
            if chunk and chunk in norm_local:
                ok = True
                break
        if not ok:
            return False
    return True


def lookup_public_email(company_name: str, city: str | None, ico: str | None) -> str | None:
    """Hľadá e-mail pre firmu cez Google Search (bez API kľúča)."""
    # Zostavíme dopyt
    query_parts = [f'"{company_name}"']
    if city:
        query_parts.append(city)
    query_parts.append("@")
    query = " ".join(query_parts)

    url = f"https://www.google.com/search?q={quote(query)}&num=5"

    try:
        resp = httpx.get(url, timeout=15.0, headers=_HEADERS, follow_redirects=True)
        if resp.status_code != 200:
            return None

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Skúsime nájsť e-maily priamo v HTML
        text = resp.text
        matches = _EMAIL_RE.findall(text)
        for m in matches:
            if _email_acceptable(m, company_name):
                return m.lower()

        # 2. Skúsime nájsť odkazy, ktoré vyzerajú ako firemné weby, a prejsť ich
        for a in soup.select("a"):
            href = a.get("href", "")
            if href and isinstance(href, str) and href.startswith("/url?q="):
                # Google redirect
                real_url = href.split("/url?q=")[1].split("&")[0]
                if any(x in real_url for x in ("google.", "youtube.", "facebook.", "linkedin.")):
                    continue
                # Preskočíme registre a katalógy
                if any(d in real_url for d in _SKIP_DOMAINS):
                    continue
                try:
                    r2 = httpx.get(real_url, timeout=10.0, headers=_HEADERS, follow_redirects=True)
                    if r2.status_code == 200:
                        m2 = _EMAIL_RE.findall(r2.text)
                        for m in m2:
                            if _email_acceptable(m, company_name):
                                return m.lower()
                except Exception:
                    continue
            return None
    except Exception:
        return None


# --- Chýbajúce funkcie (aby importy v iných súboroch fungovali) ---


_CONSUMER_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "seznam.cz",
    "centrum.cz",
    "azet.sk",
    "t-com.sk",
    "mail.t-com.sk",
    "telekom.sk",
}


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _ascii(text).lower())


def _extract_card_email(card, company_name: str | None = None) -> str | None:
    # Find mailto link
    email = None
    for a in card.select("a[href^='mailto:']"):
        href = a.get("href", "")
        if isinstance(href, str):
            val = href[len("mailto:") :].split("?")[0].strip()
            if val:
                email = val
                break
    if not email or _is_junk(email):
        return None
    local, _, domain = email.partition("@")
    domain = domain.lower()
    is_consumer = domain in _CONSUMER_EMAIL_DOMAINS
    if is_consumer:
        if not company_name:
            return None
        norm_company = _normalize_for_match(company_name)
        norm_local = _normalize_for_match(local)
        # require at least 3 consecutive chars from company name in local part
        ok = False
        for i in range(len(norm_company) - 2):
            chunk = norm_company[i : i + 3]
            if chunk and chunk in norm_local:
                ok = True
                break
        if not ok:
            return None
    return email.lower()


def _extract_card_name(card, company_name: str | None = None) -> str | None:
    a = card.select_one('a[href*="/firmy/"]')
    if a is None:
        return None
    return a.get_text(strip=True) or None


def _extract_card_website(card, company_name: str | None = None) -> str | None:
    # Prefer dedicated li.link slot
    link_li = card.select_one("li.link a")
    if link_li is not None:
        href = link_li.get("href")
        if isinstance(href, str) and href.startswith("http"):
            if "zlatestranky" not in href:
                return href
    # Fallback: microdata span[itemprop=url]
    span = card.select_one('span[itemprop="url"]')
    if span is not None:
        # find enclosing anchor
        parent = span.find_parent("a")
        if parent is not None:
            href = parent.get("href")
            if isinstance(href, str) and href.startswith("http") and "zlatestranky" not in href:
                return href
    # Also check any anchor with itemprop url span
    for a in card.select("a"):
        span = a.select_one('span[itemprop="url"]')
        if span is not None:
            href = a.get("href")
            if isinstance(href, str) and href.startswith("http") and "zlatestranky" not in href:
                return href
    # Last resort: first external non-register link
    for a in card.select("a[href^='http']"):
        href = a.get("href", "")
        if isinstance(href, str):
            if "zlatestranky" in href or "indexpodnikatela" in href:
                continue
            return href
    return None


def _extract_joomla_cloak_email(text) -> str | None:
    import html as _html

    if not text:
        return None
    # Extract all single-quoted string literals and unescape HTML entities.
    parts = re.findall(r"'([^']*)'", str(text))
    if not parts:
        return None
    joined = "".join(_html.unescape(p) for p in parts)
    m = _EMAIL_RE.search(joined)
    if not m:
        return None
    email = m.group(0).lower()
    if _is_junk(email):
        return None
    return email


def _normalize_name(text: str) -> str:
    return text.lower().strip()


def _get(url: str, timeout: float = 15.0):
    import httpx

    return httpx.get(url, timeout=timeout, headers=_HEADERS)
