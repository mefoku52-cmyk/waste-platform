"""External web-search gateway contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class WebSearchRequest:
    request_id: str
    query: str
    locale: str | None = None
    region: str | None = None
    max_results: int = 10
    safe_search: bool = True

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.query.strip():
            raise ValueError("query is required")
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")


@dataclass(frozen=True, slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.url.strip():
            raise ValueError("url is required")


@dataclass(frozen=True, slots=True)
class WebSearchResponse:
    request_id: str
    results: tuple[WebSearchResult, ...] = field(default_factory=tuple)


class WebSearchGateway(ABC):
    """External search boundary.

    Search results are untrusted external data.
    They must never directly become executable instructions.
    """

    @abstractmethod
    async def search(self, request: WebSearchRequest) -> WebSearchResponse:
        raise NotImplementedError
