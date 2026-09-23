"""External web infrastructure boundaries."""

from .web_result_normalizer import NormalizedWebResult, WebResultNormalizer
from .web_search_gateway import (
    WebSearchGateway,
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)

__all__ = [
    "NormalizedWebResult",
    "WebResultNormalizer",
    "WebSearchGateway",
    "WebSearchRequest",
    "WebSearchResponse",
    "WebSearchResult",
]
