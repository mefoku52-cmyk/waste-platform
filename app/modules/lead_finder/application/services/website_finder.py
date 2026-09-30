"""Find company website via Google Custom Search.

Používa GoogleWebSearchGateway (agent_platform) na nájdenie
firemného webu z názvu firmy + mesta. Filtruje katalógy
a sociálne siete (facebook, linkedin, atď.).

Výsledok sa potom posiela do LegalEmailFinder (scraper).
"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urlparse

from app.modules.agent_platform.infrastructure.web.web_search_gateway import (
    GoogleWebSearchGateway,
    WebSearchRequest,
)

logger = logging.getLogger(__name__)

# Domény, ktoré NIE SÚ firemný web — preskočiť
_SKIP_DOMAINS = (
    "facebook.com",
    "fb.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
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
    "wikipedia.org",
    "wikidata.org",
    "google.com",
    "maps.google.com",
    "yandex.com",
    "bing.com",
    "duckduckgo.com",
    "profesia.sk",
    "bazos.sk",
    "bazos.cz",
    "heureka.sk",
    "heureka.cz",
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
    """Google CSE -> URL firemného webu."""

    def __init__(self, gateway: GoogleWebSearchGateway | None = None) -> None:
        self._gateway = gateway or GoogleWebSearchGateway()

    def is_available(self) -> bool:
        return self._gateway.is_available()

    async def find_website(
        self,
        *,
        company_name: str,
        city: str | None = None,
    ) -> str | None:
        """Vráti URL firemného webu alebo None."""
        if not self.is_available():
            return None
        if not company_name.strip():
            return None

        # Query: nazov firmy + mesto
        parts = [company_name.strip()]
        if city and city.strip():
            parts.append(city.strip())
        query = " ".join(parts)

        try:
            response = await self._gateway.search(
                WebSearchRequest(
                    request_id=str(uuid.uuid4()),
                    query=query,
                    max_results=10,
                )
            )
        except Exception:
            logger.exception("Google search failed for %s", query)
            return None

        for result in response.results:
            if not result.url:
                continue
            if _is_skippable_domain(result.url):
                continue
            return result.url

        return None
