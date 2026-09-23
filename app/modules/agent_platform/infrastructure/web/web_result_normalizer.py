"""Normalization boundary for external search results."""

from dataclasses import dataclass

from .web_search_gateway import WebSearchResult


@dataclass(frozen=True, slots=True)
class NormalizedWebResult:
    title: str
    url: str
    snippet: str
    source: str


class WebResultNormalizer:
    """Converts external results into safe internal records.

    This class deliberately does not interpret page content as instructions.
    """

    @staticmethod
    def normalize(result: WebSearchResult) -> NormalizedWebResult:
        return NormalizedWebResult(
            title=result.title.strip(),
            url=result.url.strip(),
            snippet=(result.snippet or "").strip(),
            source=(result.source or "external").strip(),
        )
