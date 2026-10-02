from __future__ import annotations

import asyncio
import importlib
import logging
import re
from urllib.parse import unquote, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebsiteFinder:
    """
    Finds a company's official website using DuckDuckGo search.

    The public interface intentionally stays compatible with the existing
    lead discovery/backfill services.
    """

    _SKIP_DOMAINS = (
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
        "discord.com",
        "whatsapp.com",
        "telegram.org",
        "t.me",
        "github.com",
        "gitlab.com",
        "stackoverflow.com",
        "medium.com",
        "amazon.com",
        "microsoft.com",
        "apple.com",
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "wikipedia.org",
        "wikidata.org",
        "seznam.cz",
        # Slovak company registers/directories
        "valida.sk",
        "finstat.sk",
        "orsr.sk",
        "orsf.sk",
        "foaf.sk",
        "peniaze.sk",
        "registeruz.sk",
        "findat.sk",
        "firmy.sk",
        "firmydata.sk",
        "zlatestranky.sk",
        "katalogfiriem.sk",
        "indexpodnikatela.sk",
        "firemnyportal.sk",
        "odpady-portal.sk",
        "zoznam.sk",
        "azet.sk",
        "topky.sk",
        "podnikajte.sk",
        "podnikam.sk",
        "bazos.sk",
        "heureka.sk",
        "profesia.sk",
        "example.com",
        "example.org",
        "example.net",
    )

    _SKIP_TITLE_PATTERNS = (
        "obchodný register",
        "register firiem",
        "firemný register",
        "company profile",
        "profil firmy",
        "firemný profil",
        "finančný report",
        "katalóg firiem",
        "adresár firiem",
        "výpis z obchodného registra",
    )

    def __init__(self, *, timeout: float = 20.0) -> None:
        self._timeout = timeout

    @staticmethod
    def is_available() -> bool:
        for module_name in ("ddgs", "duckduckgo_search"):
            try:
                importlib.import_module(module_name)
                return True
            except ImportError:
                continue
        logger.warning("duckduckgo-search (ddgs) not installed")
        return False

    @staticmethod
    def _normalise_name(value: str) -> str:
        value = value.lower()
        value = value.replace("&", " and ")

        # Remove Slovak/Czech legal suffixes.
        value = re.sub(
            r"\b(?:s\.?\s*r\.?\s*o\.?|a\.?\s*s\.?|spol\.?\s*s\.?\s*r\.?\s*o\.?)\b",
            " ",
            value,
        )

        value = re.sub(r"[^a-z0-9áäčďéěíĺľňóôŕšťúýž]+", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @classmethod
    def _company_tokens(cls, company_name: str) -> list[str]:
        normalised = cls._normalise_name(company_name)
        return [token for token in normalised.split() if len(token) >= 2]

    @classmethod
    def _domain(cls, url: str) -> str:
        try:
            return urlparse(url).netloc.lower().split(":")[0]
        except Exception:
            return ""

    @classmethod
    def _is_skipped_domain(cls, url: str) -> bool:
        domain = cls._domain(url)
        if not domain:
            return True

        return any(
            domain == blocked or domain.endswith("." + blocked) for blocked in cls._SKIP_DOMAINS
        )

    @classmethod
    def _is_skipped_title(cls, title: str) -> bool:
        lowered = title.lower()
        return any(pattern in lowered for pattern in cls._SKIP_TITLE_PATTERNS)

    @classmethod
    def _score_result(
        cls,
        *,
        company_name: str,
        ico: str | None,
        title: str,
        url: str,
    ) -> int:
        title_norm = cls._normalise_name(title)
        company_norm = cls._normalise_name(company_name)

        tokens = cls._company_tokens(company_name)

        score = 0

        # Strong signal: complete normalized company name in title.
        if company_norm and company_norm in title_norm:
            score += 50

        # Token matching.
        score += sum(10 for token in tokens if token in title_norm)

        # IČO appearing in title or URL is a strong signal.
        if ico:
            clean_ico = re.sub(r"\D", "", ico)
            haystack = f"{title} {url}"
            if clean_ico and clean_ico in haystack:
                score += 30

        # Prefer ordinary HTTPS websites.
        if url.lower().startswith("https://"):
            score += 2

        return score

    @staticmethod
    def _decode_url(url: str) -> str:
        """
        Keep this defensive decoder for compatibility with URLs returned by
        search providers. DuckDuckGo may return final URLs directly; the
        `uddg` wrapper is unwrapped when present.
        """
        try:
            value = unquote(url)

            # Some providers wrap URLs in a query parameter.
            parsed = urlparse(value)
            query = parsed.query

            for key in ("uddg", "url", "target"):
                match = re.search(
                    rf"(?:^|&){re.escape(key)}=([^&]+)",
                    query,
                )
                if match:
                    return unquote(match.group(1))

            return value
        except Exception:
            return url

    def _search(self, query: str) -> list[dict]:
        """
        Search DuckDuckGo for possible official company websites.

        This method only discovers candidates. It does NOT decide whether
        a result is the company's official website. That decision belongs
        exclusively to find_website() direct verification.

        Synchronous by design — callers run it via asyncio.to_thread.
        """
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
                results = list(ddgs.text(query, max_results=10))
        except Exception:
            logger.exception("DDGS.text failed for %s", query)
            return []

        logger.info(
            "DuckDuckGo search: query=%r results=%d",
            query,
            len(results),
        )

        return results

    async def find_website(
        self,
        *,
        company_name: str,
        city: str | None = None,
        ico: str | None = None,
    ) -> str | None:
        """
        Discover candidate URLs through DuckDuckGo and verify them directly.

        Search-engine mentions are not treated as proof that a domain is
        the company's official website. Candidate pages are fetched and
        their HTML title/body are checked for the company identity.
        """

        if not self.is_available():
            logger.error(
                "WebsiteFinder unavailable: neither ddgs nor duckduckgo_search is installed"
            )
            return None

        # Discovery queries are deliberately broad enough to find
        # small company websites, but the results are still treated only
        # as candidates. Direct website verification below is mandatory.
        queries: list[str] = []

        if ico:
            queries.extend(
                [
                    f'"{company_name}" "{ico}" kontakt',
                    f'"{company_name}" "{ico}" web',
                    f'"{company_name}" "{ico}" email',
                    f'"{company_name}" IČO "{ico}" kontakt',
                    f'"{company_name}" IČO "{ico}" web',
                    f'"{company_name}" IČO "{ico}" email',
                    f'"{ico}" kontakt',
                    f'"{ico}" web',
                    f'"{ico}" email',
                ]
            )

        queries.extend(
            [
                f'"{company_name}" kontakt',
                f'"{company_name}" web',
                f'"{company_name}" email',
            ]
        )

        if city:
            queries.extend(
                [
                    f'"{company_name}" "{city}" kontakt',
                    f'"{company_name}" "{city}" web',
                    f'"{company_name}" "{city}" email',
                ]
            )

        # Keep the exact-name search as a final fallback.
        queries.append(f'"{company_name}"')

        queries = list(dict.fromkeys(queries))

        all_results: list[dict] = []

        for query in queries:
            found = await asyncio.to_thread(
                self._search,
                query,
            )
            if not found:
                logger.warning("DuckDuckGo vratilo 0 vysledkov pre query: %s", query)
            all_results.extend(found)

        if not all_results:
            logger.warning(
                "No DuckDuckGo results for company=%r ico=%r city=%r",
                company_name,
                ico,
                city,
            )
            return None

        company_tokens = self._company_tokens(company_name)

        # Very short/generic company names are unsafe to resolve
        # automatically unless the search result gives strong identity
        # evidence. Example: "LS a. s.".
        meaningful_tokens = [token for token in company_tokens if len(token) >= 4]

        if not meaningful_tokens:
            logger.warning(
                "Company name too generic for automatic website resolution: %r",
                company_name,
            )
            return None

        candidates: list[tuple[int, str, dict]] = []
        seen_urls: set[str] = set()

        for result in all_results:
            title = result.get("title", "").strip()
            raw_url = result.get("href", "").strip()

            if not title or not raw_url:
                continue

            url = self._decode_url(raw_url)

            if url in seen_urls:
                continue

            seen_urls.add(url)

            if self._is_skipped_domain(url):
                continue

            if self._is_skipped_title(title):
                continue

            # Only test normal HTTP(S) web pages.
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                continue

            # ----------------------------------------------------------
            # DIRECT WEBSITE VERIFICATION
            # ----------------------------------------------------------
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Linux; Android 16) "
                        "AppleWebKit/537.36 Chrome/140.0 Mobile Safari/537.36"
                    ),
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.7",
                }

                async with httpx.AsyncClient(
                    timeout=self._timeout,
                    follow_redirects=True,
                    headers=headers,
                ) as client:
                    response = await client.get(url)

                if response.status_code >= 400:
                    continue

                content_type = response.headers.get("content-type", "").lower()

                if "html" not in content_type:
                    continue

                final_url = str(response.url)

                if self._is_skipped_domain(final_url):
                    continue

                soup = BeautifulSoup(
                    response.text[:1_500_000],
                    "html.parser",
                )

                page_title = soup.title.get_text(" ", strip=True) if soup.title else ""

                page_text = soup.get_text(
                    " ",
                    strip=True,
                )

            except Exception:
                logger.debug(
                    "Direct website verification failed: %s",
                    url,
                    exc_info=True,
                )
                continue

            # ----------------------------------------------------------
            # COMPANY IDENTITY CHECK
            # ----------------------------------------------------------
            page_norm = self._normalise_name(f"{page_title} {page_text}")

            title_norm = self._normalise_name(page_title)

            title_matches = sum(1 for token in meaningful_tokens if token in title_norm)

            page_matches = sum(1 for token in meaningful_tokens if token in page_norm)

            full_company_name = self._normalise_name(company_name)

            full_name_in_title = bool(full_company_name and full_company_name in title_norm)

            full_name_on_page = bool(full_company_name and full_company_name in page_norm)

            # IČO is only strong evidence when explicitly labelled.
            clean_ico = re.sub(r"\D", "", ico or "")
            ico_on_page = False

            if clean_ico:
                ico_on_page = bool(
                    re.search(
                        rf"\b(?:iČo|ico)\s*[:.]?\s*"
                        rf"{re.escape(clean_ico)}\b",
                        page_text,
                        re.IGNORECASE,
                    )
                )

            # Reject pages that explicitly identify a different IČO.
            if clean_ico:
                other_icos = re.findall(
                    r"\b(?:iČo|ico)\s*[:.]?\s*(\d{8})\b",
                    page_text,
                    re.IGNORECASE,
                )

                if any(found_ico != clean_ico for found_ico in other_icos):
                    continue

            # ----------------------------------------------------------
            # ACCEPTANCE RULE
            # ----------------------------------------------------------
            #
            # We need actual company identity on the fetched page.
            #
            # Strong:
            #   full company name in title/page
            #   OR exact IČO + meaningful company token
            #
            # Weak search-result-only matches are rejected.
            # ----------------------------------------------------------

            if full_name_in_title:
                score = 100

            elif full_name_on_page:
                score = 80

            elif ico_on_page and page_matches >= 2:
                score = 75

            elif title_matches >= 2 and page_matches >= 2:
                score = 60

            else:
                continue

            # Prefer the domain root as the stored company website.
            clean_url = f"{parsed.scheme}://{parsed.netloc}/"

            if final_url.rstrip("/") != url.rstrip("/"):
                final_parsed = urlparse(final_url)

                if final_parsed.netloc:
                    clean_url = f"{final_parsed.scheme}://{final_parsed.netloc}/"

            candidates.append(
                (
                    score,
                    clean_url,
                    {
                        **result,
                        "verified_title": page_title,
                        "verified_url": final_url,
                    },
                )
            )

        if not candidates:
            logger.warning(
                "DuckDuckGo candidates found, but no candidate passed "
                "DIRECT WEBSITE VERIFICATION: company=%r ico=%r",
                company_name,
                ico,
            )
            return None

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_url, best_result = candidates[0]

        logger.info(
            "Verified company website: company=%r ico=%r score=%s title=%r url=%s",
            company_name,
            ico,
            best_score,
            best_result.get("verified_title"),
            best_url,
        )

        return best_url


__all__ = ["WebsiteFinder"]

# Backward-compatible module-level API used by unit tests and older callers.
_SKIP_DOMAINS = WebsiteFinder._SKIP_DOMAINS


def _is_skippable_domain(url: str) -> bool:
    return WebsiteFinder._is_skipped_domain(url)
