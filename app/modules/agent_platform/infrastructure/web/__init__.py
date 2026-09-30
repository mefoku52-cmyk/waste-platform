"""External web infrastructure boundaries."""

from .web_result_normalizer import NormalizedWebResult, WebResultNormalizer
from .web_search_gateway import (
    GoogleWebSearchGateway,
    WebSearchGateway,
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)

__all__ = [
    "GoogleWebSearchGateway",
    "NormalizedWebResult",
    "WebResultNormalizer",
    "WebSearchGateway",
    "WebSearchRequest",
    "WebSearchResponse",
    "WebSearchResult",
]
