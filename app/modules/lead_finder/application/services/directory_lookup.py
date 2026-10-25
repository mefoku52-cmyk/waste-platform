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
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=_HEADERS) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return None

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. Skúsime nájsť e-maily priamo v HTML
            text = soup.get_text(" ", strip=True)
            matches = _EMAIL_RE.findall(text)
            for m in matches:
                if not _is_junk(m):
                    return m.lower()

            # 2. Skúsime nájsť odkazy, ktoré vyzerajú ako firemné weby, a prejsť ich
            for a in soup.select("a"):
                href = a.get("href", "")
                if href and isinstance(href, str) and href.startswith("/url?q="):
                    # Google redirect
                    real_url = href.split("/url?q=")[1].split("&")[0]
                    if any(
                        x in real_url for x in ("google.", "youtube.", "facebook.", "linkedin.")
                    ):
                        continue
                    try:
                        r2 = client.get(real_url, timeout=10.0)
                        if r2.status_code == 200:
                            m2 = _EMAIL_RE.findall(r2.text)
                            for m in m2:
                                if not _is_junk(m):
                                    return m.lower()
                    except Exception:
                        continue
            return None
    except Exception:
        return None


# --- Chýbajúce funkcie (aby importy v iných súboroch fungovali) ---


def _extract_card_email(card, company_name: str | None = None) -> str | None:
    return None


def _extract_card_name(card, company_name: str | None = None) -> str | None:
    return None


def _extract_card_website(card, company_name: str | None = None) -> str | None:
    return None


def _extract_joomla_cloak_email(text) -> str | None:
    return None


def _normalize_name(text: str) -> str:
    return text.lower().strip()


def _get(url: str, timeout: float = 15.0):
    import httpx

    return httpx.get(url, timeout=timeout, headers=_HEADERS)
