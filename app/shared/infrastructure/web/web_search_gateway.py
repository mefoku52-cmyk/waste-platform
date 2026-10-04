"""Google Custom Search JSON API gateway for web search.

Requires:
- GOOGLE_CSE_API_KEY
- GOOGLE_CSE_ID (Programmable Search Engine ID)
Free tier: 100 queries/day.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


@dataclass(frozen=True, slots=True)
class WebSearchRequest:
    request_id: str
    query: str
    max_results: int = 10

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.query.strip():
            raise ValueError("query is required")
        if self.max_results < 1 or self.max_results > 10:
            raise ValueError("max_results must be between 1 and 10")


@dataclass(frozen=True, slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.url.strip():
            raise ValueError("url is required")


@dataclass(frozen=True, slots=True)
class WebSearchResponse:
    request_id: str
    results: tuple[WebSearchResult, ...] = field(default_factory=tuple)


class GoogleWebSearchGateway:
    """Google Custom Search JSON API gateway."""

    def __init__(self, *, api_key: str | None = None, cse_id: str | None = None) -> None:
        self._api_key = (api_key or os.getenv("GOOGLE_CSE_API_KEY", "")).strip()
        self._cse_id = (cse_id or os.getenv("GOOGLE_CSE_ID", "")).strip()

    def is_available(self) -> bool:
        return bool(self._api_key and self._cse_id)

    async def search(self, request: WebSearchRequest) -> WebSearchResponse:
        if not self.is_available():
            return WebSearchResponse(request_id=request.request_id)

        params = {
            "key": self._api_key,
            "cx": self._cse_id,
            "q": request.query,
            "num": min(request.max_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(GOOGLE_CSE_URL, params=params)
                if resp.status_code >= 400:
                    return WebSearchResponse(request_id=request.request_id)
                data = resp.json()
        except Exception:
            return WebSearchResponse(request_id=request.request_id)

        items = data.get("items", []) or []
        results = []
        for item in items:
            title = str(item.get("title", "")).strip()
            url = str(item.get("link", "")).strip()
            snippet = str(item.get("snippet", "")).strip() or None
            if title and url:
                results.append(WebSearchResult(title=title, url=url, snippet=snippet))

        return WebSearchResponse(request_id=request.request_id, results=tuple(results))


# Backward-compat alias pre existujuce importy
WebSearchGateway = GoogleWebSearchGateway
