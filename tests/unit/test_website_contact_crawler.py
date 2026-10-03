"""Testy website_contact_crawler - bez siete.

Prvá časť pokrýva cestu, ktorá sa nesmie dotknúť HTTP: neplatná URL
musí vrátiť (None, None) a nesmie spraviť ani jeden request.

Druhá časť testuje extrakciu, validáciu, robots.txt a cache správanie
nad fixture súbormi. Všetky HTTP volania sú mockované
(`monkeypatch.setattr`), takže žiadny test nesiahne na sieť.
"""

from pathlib import Path

import httpx
import pytest

from app.modules.lead_finder.application.services import (
    website_contact_crawler as crawler,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "crawler"

_COMPANY = "EKOL RECYKLACNE SYSTEMY s.r.o."
_SITE = "https://ekolpresov.sk"


def load_fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


class FakeResponse:
    """Minimálna náhrada httpx.Response pre mockované volania."""

    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        content_type: str = "text/html",
        url: str = _SITE + "/",
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = {"content-type": content_type}
        self.url = url


@pytest.fixture(autouse=True)
def crawler_state(monkeypatch):
    """Izoluj cache a vypni Redis; spánky medzi requestami preskoč."""
    crawler._MEMORY_CACHE.clear()
    monkeypatch.setattr(crawler, "_REDIS_DISABLED", True)
    monkeypatch.setattr(crawler.time, "sleep", lambda seconds: None)

    yield

    crawler._MEMORY_CACHE.clear()


@pytest.fixture
def no_network(monkeypatch):
    """Zakaždé HTTP volanie zlyhá a zapíše sa do zoznamu."""
    calls: list = []

    def _fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError(f"HTTP request attempted: {args} {kwargs}")

    monkeypatch.setattr(httpx, "get", _fail)

    return calls


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "not a url",
        "localhost",
        "ftp://example.com",
        "https://",
        "javascript:alert(1)",
    ],
)
def test_crawl_contact_email_invalid_url_returns_none(url, no_network):
    """Neplatná URL -> (None, None) a žiadny HTTP request."""
    assert crawler.crawl_contact_email(url, "EKOL - recyklacne systemy") == (
        None,
        None,
    )
    assert no_network == []


def test_crawl_contact_email_empty_company_returns_none(no_network):
    """Prázdny názov firmy -> (None, None) bez HTTP requestu."""
    assert crawler.crawl_contact_email("https://ekolpresov.sk", "   ") == (
        None,
        None,
    )
    assert no_network == []


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.Firma.sk/kontakt?a=1", "https://firma.sk"),
        ("http://www.firma.sk/kontakt", "http://firma.sk"),
        ("firma.sk/kontakt", "https://firma.sk"),
        ("https://firma.sk:8443/x", "https://firma.sk"),
        ("https://user:pw@firma.sk/x", "https://firma.sk"),
    ],
)
def test_normalize_origin_keeps_scheme_strips_rest(url, expected):
    assert crawler._normalize_origin(url) == expected


@pytest.mark.parametrize("url", ["", "   ", "localhost", "ftp://firma.sk"])
def test_normalize_origin_invalid_returns_none(url):
    assert crawler._normalize_origin(url) is None


# --- Extrakcia emailov z fixture HTML ----------------------------------


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("homepage_with_mailto.html", ["info@ekolpresov.sk"]),
        ("kontakt_with_obfuscated.html", ["info@ekolpresov.sk"]),
        ("page_without_email.html", []),
        ("json_ld_contact.html", ["info@ekolpresov.sk"]),
    ],
)
def test_extract_emails_from_html(fixture, expected):
    """mailto, Joomla cloak, prázdna stránka a JSON-LD text."""
    assert crawler._extract_emails_from_html(load_fixture(fixture)) == expected


def test_extract_json_ld_email_from_fixture():
    """schema.org 'mailto:' prefix sa musí strhnúť."""
    assert crawler._extract_json_ld_email(load_fixture("json_ld_contact.html")) == [
        "info@ekolpresov.sk"
    ]


def test_extract_json_ld_email_broken_json_returns_empty():
    """Pokazený JSON blok nesmie zhodiť crawl - vráti prázdny zoznam."""
    html = '<script type="application/ld+json">{ "email": "info@ekolpresov.sk", }</script>'

    assert crawler._extract_json_ld_email(html) == []


# --- Validacia ----------------------------------------------------------


@pytest.mark.parametrize(
    ("email", "page_domain", "expected"),
    [
        # D1: email na doméne stránky.
        ("info@ekolpresov.sk", "ekolpresov.sk", True),
        # Non-free domena, ktorá sedí s názvom firmy.
        ("info@ekolpresov.sk", "", True),
        # D2: free provider, local-part sedí s názvom firmy.
        ("ekolpresov@gmail.com", "ekolpresov.sk", True),
        # D2: free provider, local-part nesedí.
        ("jan.novak@gmail.com", "ekolpresov.sk", False),
        # Non-free domena bez zhody s názvom firmy.
        ("info@unrelated.sk", "ekolpresov.sk", False),
        # Smetná adresa (marker).
        ("noreply@ekolpresov.sk", "ekolpresov.sk", False),
        # Smetná adresa (pattern).
        ("support@discord.com", "ekolpresov.sk", False),
    ],
)
def test_is_valid_email(email, page_domain, expected):
    assert crawler._is_valid_email(email, _COMPANY, page_domain) is expected


# --- robots.txt / cache / Redis ----------------------------------------


def _serve_pages(html: str, *, robots_status: int = 404, page_status: int = 200):
    """Postav fake httpx.get, ktorý obslúži robots.txt aj stránky."""
    calls: list[str] = []

    def fake_get(url, **kwargs):
        text = str(url)

        if text.endswith("/robots.txt"):
            calls.append(text)
            return FakeResponse(
                status_code=robots_status,
                text=html if robots_status == 200 else "",
                content_type="text/plain",
                url=text,
            )

        calls.append(text)
        return FakeResponse(
            status_code=page_status,
            text=html,
            content_type="text/html",
            url=text,
        )

    return fake_get, calls


def test_robots_disallow_returns_none_without_fetch(monkeypatch):
    """robots.txt zakazuje crawl -> (None, None) a žiadny fetch stránky."""
    robots_text = load_fixture("robots_disallow.html")
    fake_get, calls = _serve_pages(robots_text, robots_status=200)

    monkeypatch.setattr(httpx, "get", _assert_no_page_fetch(fake_get))

    assert crawler.crawl_contact_email(_SITE, _COMPANY) == (None, None)

    # Stiahol sa len robots.txt, žiadna firemná stránka.
    page_calls = [c for c in calls if not c.endswith("/robots.txt")]
    assert page_calls == []


def _assert_no_page_fetch(fake_get):
    """Obalí fake_get tak, že fetch stránky okamžite zlyhá."""

    def wrapper(url, **kwargs):
        text = str(url)

        if not text.endswith("/robots.txt"):
            raise AssertionError(f"page fetch attempted: {text}")

        return fake_get(url, **kwargs)

    return wrapper


def test_definitive_miss_is_cached_without_second_http(monkeypatch):
    """Negatívny výsledok sa cachuje -> druhý call bez HTTP."""
    html = load_fixture("page_without_email.html")
    fake_get, calls = _serve_pages(html)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert crawler.crawl_contact_email(_SITE, _COMPANY) == (None, None)
    first_call_count = len(calls)

    assert first_call_count > 0
    assert crawler.crawl_contact_email(_SITE, _COMPANY) == (None, None)
    assert len(calls) == first_call_count


def test_5xx_response_is_not_cached(monkeypatch):
    """Dočasné zlyhanie servera sa nesmie cachovať."""
    fake_get, _calls = _serve_pages("", page_status=503)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert crawler.crawl_contact_email(_SITE, _COMPANY) == (None, None)

    origin = crawler._normalize_origin(_SITE)
    key = crawler._hash_key(crawler._EMAIL_CACHE_PREFIX, origin)

    assert crawler._cache_get(key) is None


def test_crawler_works_without_redis(monkeypatch):
    """S vypnutým Redism musí crawler fungovať cez in-memory cache."""
    monkeypatch.setattr(crawler, "_REDIS_DISABLED", True)

    html = load_fixture("homepage_with_mailto.html")
    fake_get, _calls = _serve_pages(html)

    monkeypatch.setattr(httpx, "get", fake_get)

    assert crawler._get_redis() is None

    email, source_url = crawler.crawl_contact_email(_SITE, _COMPANY)

    assert email == "info@ekolpresov.sk"
    assert source_url is not None
