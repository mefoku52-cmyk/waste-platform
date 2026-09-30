"""Legal email discovery from public web sources.

Searches for business emails on company websites only.
Designed for B2B outreach under legitimate interest (GDPR Art. 6(1)(f)).

Requires:
- httpx
- beautifulsoup4
- (stdlib re)

No external email-extraction library is used.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Jednoduchy regex - staci pre firemne weby
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# Bezne "smetne" adresy, ktore nechceme
_JUNK_PATTERNS = (
    "example.com",
    "sentry.io",
    "wixpress.com",
    "googlemail.com",
    "@2x.png",
    "no-reply@",
    "noreply@",
    "donotreply@",
)

# Preferovane genericke firemne adresy
_GENERIC_PREFIXES = (
    "info@",
    "contact@",
    "office@",
    "predaj@",
    "obchod@",
    "kancelaria@",
)


class LegalEmailFinder:
    """Finds business emails from public company websites."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "CMEP-Bot/1.0 (+https://trc-cmep.sk/bot)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    def find_email_for_company(self, website_url: str | None) -> str | None:
        """Return the best business email found on the company website, or None."""
        if not website_url:
            return None

        url = website_url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
        except Exception:
            return None

        try:
            emails = self._extract_from_url(url)
            if not emails:
                # Skus kontakt stranku
                contact = self._find_contact_link(url)
                if contact:
                    emails = self._extract_from_url(contact)

            if not emails:
                return None

            return self._pick_best(emails)

        except Exception as exc:
            logger.debug("Email discovery failed for %s: %s", url, exc)
            return None

    def _extract_from_url(self, url: str) -> list[str]:
        try:
            resp = self._client.get(url)
        except Exception:
            return []
        if resp.status_code >= 400:
            return []
        return self._extract_from_html(resp.text)

    @staticmethod
    def _extract_from_html(html: str) -> list[str]:
        found: set[str] = set()

        # 1. Regex na cele HTML
        for m in _EMAIL_RE.findall(html):
            found.add(m.lower())

        # 2. mailto: odkazy (niekedy obfuskovane)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # BeautifulSoup vracia str | AttributeValueList (list)
            if not isinstance(href, str):
                continue
            if href.lower().startswith("mailto:"):
                addr = href[7:].split("?")[0].strip().lower()
                if addr:
                    found.add(addr)

        # Filtrovanie odpadu
        clean: list[str] = []
        for e in found:
            if any(j in e for j in _JUNK_PATTERNS):
                continue
            # Zakladna validacia
            if len(e) > 254 or e.startswith("@") or e.endswith("."):
                continue
            clean.append(e)
        return clean

    def _find_contact_link(self, base_url: str) -> str | None:
        try:
            resp = self._client.get(base_url)
        except Exception:
            return None
        if resp.status_code >= 400:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        keywords = ("kontakt", "contact", "o-nas", "o nás", "about")
        for a in soup.find_all("a", href=True):
            href = str(a["href"]).lower()
            if any(k in href for k in keywords):
                return urljoin(base_url, a["href"])
        return None

    @staticmethod
    def _pick_best(emails: list[str]) -> str | None:
        """Preferuj genericke adresy (info@, contact@, ...) pred osobnymi."""
        if not emails:
            return None
        for prefix in _GENERIC_PREFIXES:
            for e in emails:
                if e.startswith(prefix):
                    return e
        return emails[0]

    def close(self) -> None:
        self._client.close()
