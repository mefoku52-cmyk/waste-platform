"""Find company website via DuckDuckGo search.

Používa `duckduckgo-search` (bez API kľúča, bez registrácie).
Filtruje katalógy a sociálne siete (facebook, linkedin, atď.).

Výsledok sa potom posiela do AsyncLegalEmailFinder (scraper).
"""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Domény, ktoré NIE SÚ firemný web — preskočiť
_SKIP_DOMAINS = (
    # Socialne siete
    "facebook.com",
    "fb.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "pinterest.com",
    "snapchat.com",
    "reddit.com",
    # Chat a komunikacia
    "discord.com",
    "discord.gg",
    "whatsapp.com",
    "wa.me",
    "telegram.org",
    "t.me",
    "signal.org",
    "slack.com",
    "zoom.us",
    "skype.com",
    "messenger.com",
    # Vyvoj a cloud
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "stackoverflow.com",
    "medium.com",
    "substack.com",
    "twitch.tv",
    "amazon.com",
    "amazon.de",
    "aws.amazon.com",
    "microsoft.com",
    "office.com",
    "apple.com",
    "icloud.com",
    # Markety a katalogy
    "alza.sk",
    "alza.cz",
    "mall.sk",
    "mall.cz",
    "ebay.com",
    "ebay.de",
    "heureka.sk",
    "heureka.cz",
    "bazos.sk",
    "bazos.cz",
    "profesia.sk",
    # Slovenske katalogy firiem
    "zoznam.sk",
    "azet.sk",
    "topky.sk",
    "firmy.sk",
    "firmydata.sk",
    "finstat.sk",
    "orsr.sk",
    "zlatestranky.sk",
    "katalogfiriem.sk",
    "indexpodnikatela.sk",
    "podnikajte.sk",
    "podnikam.sk",
    # Wikipedie a vyhladavace
    "wikipedia.org",
    "wikidata.org",
    "wikimedia.org",
    "google.com",
    "google.sk",
    "maps.google.com",
    "yandex.com",
    "yandex.ru",
    "bing.com",
    "duckduckgo.com",
    "seznam.cz",
    "centrum.cz",
    "atlas.cz",
    "hst.link",  # fake "email" domena
    "example.com",
    "example.org",
    "example.net",
)


def _is_skippable_domain(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return True
    if not host:
        return True
    return any(skip in host for skip in _SKIP_DOMAINS)


class WebsiteFinder:
    """DuckDuckGo search -> URL firemného webu."""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    def is_available(self) -> bool:
        import importlib

        for module_name in ("ddgs", "duckduckgo_search"):
            try:
                importlib.import_module(module_name)
                return True
            except ImportError:
                continue
        logger.warning("duckduckgo-search (ddgs) not installed")
        return False

    async def find_website(
        self,
        *,
        company_name: str,
        city: str | None = None,
    ) -> str | None:
        """Vráti URL firemného webu alebo None."""
        if not company_name.strip():
            return None

        # Query: nazov firmy + mesto
        parts = [company_name.strip()]
        if city and city.strip():
            parts.append(city.strip())
        query = " ".join(parts)

        try:
            results = await asyncio.to_thread(self._search, query)
        except Exception:
            logger.exception("DuckDuckGo search failed for %s", query)
            return None

        for result in results:
            url = str(result.get("href") or result.get("url") or "").strip()
            if not url:
                continue
            if _is_skippable_domain(url):
                continue
            return url

        return None

    def _search(self, query: str) -> list[dict]:
        """Synchrónny DuckDuckGo search — beží v to_thread."""
        import importlib

        DDGS = None
        for module_name in ("ddgs", "duckduckgo_search"):
            try:
                module = importlib.import_module(module_name)
                DDGS = getattr(module, "DDGS", None)
                if DDGS is not None:
                    break
            except ImportError:
                continue

        if DDGS is None:
            logger.error("Neither ddgs nor duckduckgo_search is installed")
            return []

        try:
            with DDGS(timeout=self._timeout) as ddgs:
                return list(ddgs.text(query, max_results=10))
        except Exception:
            logger.exception("DDGS.text failed for %s", query)
            return []
