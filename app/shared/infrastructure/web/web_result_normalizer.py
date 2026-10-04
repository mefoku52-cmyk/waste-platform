"""Normalization of external web search results."""

from dataclasses import dataclass

from .web_search_gateway import WebSearchResult


@dataclass(frozen=True, slots=True)
class NormalizedWebResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


class WebResultNormalizer:
    """Converts raw web results into safe internal records."""

    @staticmethod
    def normalize(result: WebSearchResult) -> NormalizedWebResult:
        return NormalizedWebResult(
            title=result.title.strip()[:300],
            url=result.url.strip()[:2000],
            snippet=(result.snippet or "").strip()[:500],
        )
