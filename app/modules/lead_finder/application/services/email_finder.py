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
    "example.org",
    "example.net",
    "sentry.io",
    "wixpress.com",
    "@2x.png",
    "@2x.jpg",
    "@3x.png",
    "no-reply@",
    "noreply@",
    "donotreply@",
    "do-not-reply@",
    "discord.com",
    "discord.gg",
    "github.com",
    "gitlab.com",
    "reddit.com",
    "stackoverflow.com",
    "hst.link",
    "@sentry",
    "@wixpress",
    "wix.com",
    "shopify.com",
    "wordpress.com",
    "wixsite.com",
    "weebly.com",
    "squarespace.com",
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


# Free email providers — nie su firemne, pre B2B outreach nemaju hodnotu
_FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.de",
    "yahoo.fr",
    "hotmail.com",
    "hotmail.co.uk",
    "hotmail.sk",
    "outlook.com",
    "outlook.sk",
    "live.com",
    "live.sk",
    "msn.com",
    "gmx.com",
    "gmx.at",
    "gmx.de",
    "gmx.net",
    "mail.com",
    "email.com",
    "protonmail.com",
    "proton.me",
    "icloud.com",
    "me.com",
    "mac.com",
    "centrum.sk",
    "azet.sk",
    "zoznam.sk",
    "post.sk",
    "atlas.sk",
    "pobox.sk",
    "inbox.sk",
    "mail.sk",
    "seznam.cz",
    "email.cz",
    "centrum.cz",
    "atlas.cz",
    "wp.pl",
    "o2.pl",
    "interia.pl",
    # Slovak consumer/telco mail — not B2B company addresses
    "t-com.sk",
    "mail.t-com.sk",
    "telekom.sk",
    "orangemail.sk",
    "o2.sk",
    "o2online.sk",
}


def _is_free_email(email: str) -> bool:
    """True ak email je z free providera (gmail, yahoo, atd.)."""
    try:
        domain = email.rsplit("@", 1)[1].lower()
    except (IndexError, AttributeError):
        return True
    return domain in _FREE_EMAIL_DOMAINS


def _email_matches_company(email: str, company_name: str) -> bool:
    """True ak email domena alebo lokalna cast suvisi s nazvom firmy.

    Priklad:
      email='info@djservice.sk', company='D-J service s.r.o.' -> True
      email='support@discord.com', company='D-J service s.r.o.' -> False
      email='info@ekol.sk', company='EKOL - recyklacne systemy' -> True
    """
    try:
        local, domain = email.rsplit("@", 1)
    except (ValueError, AttributeError):
        return False

    local = local.lower()
    domain = domain.lower()

    # Normalizuj nazov firmy
    name = company_name.lower()
    # Odstran bezne pravne formy
    for suffix in (
        " s.r.o.",
        " s. r. o.",
        " s.r.o",
        " sro",
        " a.s.",
        " a. s.",
        " as",
        " k.s.",
        " v.o.s.",
        " o.z.",
        " n.o.",
        " jsa",
    ):
        name = name.replace(suffix, " ")
    # Odstran interpunkciu
    import re

    name = re.sub(r"[^a-z0-9\s]", " ", name)
    words = [w for w in name.split() if len(w) >= 3]

    if not words:
        return False

    # Skontroluj ci aspon jedno slovo z nazvu je v domena alebo local casti
    haystack = domain + " " + local
    return any(w in haystack for w in words)


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

    def find_email_for_company(
        self,
        website_url: str | None,
        company_name: str | None = None,
    ) -> str | None:
        """Return the best business email found on the company website, or None.

        Ak je company_name zadany, filtruj aj podla suvislosti s firmou.
        """
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

            filtered = LegalEmailFinder._filter_emails(emails, company_name)
            if not filtered:
                return None
            return self._pick_best(filtered)

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
    def _filter_emails(emails: list[str], company_name: str | None) -> list[str]:
        """Filtruj: ziadny free provider + musi mat suvislost s firmou."""
        result: list[str] = []
        for e in emails:
            if _is_free_email(e):
                continue
            if company_name and not _email_matches_company(e, company_name):
                continue
            result.append(e)
        return result

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


class AsyncLegalEmailFinder:
    """Async verzia — neblokuje event loop. Pouziva httpx.AsyncClient.

    Odporucana pre FastAPI async endpoints. Vytvor raz, zavri raz.
    """

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "CMEP-Bot/1.0 (+https://trc-cmep.sk/bot)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
        return self._client

    async def find_email_for_company(
        self,
        website_url: str | None,
        company_name: str | None = None,
    ) -> str | None:
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
            emails = await self._extract_from_url(url)
            if not emails:
                contact = await self._find_contact_link(url)
                if contact:
                    emails = await self._extract_from_url(contact)

            if not emails:
                return None

            filtered = LegalEmailFinder._filter_emails(emails, company_name)
            if not filtered:
                return None
            return self._pick_best(filtered)

        except Exception as exc:
            logger.debug("Email discovery failed for %s: %s", url, exc)
            return None

    async def _extract_from_url(self, url: str) -> list[str]:
        try:
            client = await self._get_client()
            resp = await client.get(url)
        except Exception:
            return []
        if resp.status_code >= 400:
            return []
        return self._extract_from_html(resp.text)

    async def _find_contact_link(self, base_url: str) -> str | None:
        try:
            client = await self._get_client()
            resp = await client.get(base_url)
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

    _extract_from_html = staticmethod(LegalEmailFinder._extract_from_html)
    _pick_best = staticmethod(LegalEmailFinder._pick_best)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
