import pytest

from app.shared.infrastructure.web.web_result_normalizer import (
    WebResultNormalizer,
)
from app.shared.infrastructure.web.web_search_gateway import (
    GoogleWebSearchGateway,
    WebSearchRequest,
    WebSearchResponse,
    WebSearchResult,
)


def test_web_search_request_validation():
    r = WebSearchRequest(request_id="r1", query="q", max_results=5)
    assert r.max_results == 5
    with pytest.raises(ValueError):
        WebSearchRequest(request_id=" ", query="q")
    with pytest.raises(ValueError):
        WebSearchRequest(request_id="r", query=" ")
    with pytest.raises(ValueError):
        WebSearchRequest(request_id="r", query="q", max_results=0)
    with pytest.raises(ValueError):
        WebSearchRequest(request_id="r", query="q", max_results=11)


def test_web_search_result_validation():
    r = WebSearchResult(title="t", url="u")
    assert r.snippet is None
    with pytest.raises(ValueError):
        WebSearchResult(title=" ", url="u")
    with pytest.raises(ValueError):
        WebSearchResult(title="t", url=" ")


def test_web_search_response_default():
    r = WebSearchResponse(request_id="r1")
    assert r.results == ()


def test_gateway_availability():
    g = GoogleWebSearchGateway(api_key="", cse_id="")
    assert g.is_available() is False
    g2 = GoogleWebSearchGateway(api_key="k", cse_id="c")
    assert g2.is_available() is True


@pytest.mark.asyncio
async def test_gateway_search_unavailable():
    g = GoogleWebSearchGateway(api_key="", cse_id="")
    resp = await g.search(WebSearchRequest(request_id="r1", query="q"))
    assert resp.request_id == "r1"
    assert resp.results == ()


def test_normalizer():
    raw = WebSearchResult(title="  Title  ", url="  http://x  ", snippet="  snip  ")
    out = WebResultNormalizer.normalize(raw)
    assert out.title == "Title"
    assert out.url == "http://x"
    assert out.snippet == "snip"
    assert out.source == "web"


def test_normalizer_truncation():
    raw = WebSearchResult(title="a" * 400, url="b" * 2500, snippet="c" * 600)
    out = WebResultNormalizer.normalize(raw)
    assert len(out.title) == 300
    assert len(out.url) == 2000
    assert len(out.snippet) == 500
