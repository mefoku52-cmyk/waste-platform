"""Circuit breaker pre DuckDuckGo timeout (datacenter IP block).

Produkcia bezi na Renderi (AWS datacenter IP), kde DDG timeoutuje.
Prvy timeout musi vypnut DDG pre cely proces, aby 35 firm x 13 queries
nestracalo minuty na zbytocnych timeoutoch.
"""

from types import SimpleNamespace

import pytest

from app.modules.lead_finder.application.services import website_finder
from app.modules.lead_finder.application.services.website_finder import (
    WebsiteFinder,
    _ddg_is_disabled,
)


@pytest.fixture(autouse=True)
def reset_breaker():
    """Kazdy test zacina s neresetnutym breakerom."""
    website_finder._ddg_disabled = False
    yield
    website_finder._ddg_disabled = False


class _BoomDDGS:
    """DDGS, ktory simuluje datacenter IP block."""

    calls = 0

    def __init__(self, timeout=None):
        self._timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def text(self, *_args, **_kwargs):
        type(self).calls += 1
        raise TimeoutError("https://duckduckgo.com Timed out")


class _OkDDGS(_BoomDDGS):
    def text(self, *_args, **_kwargs):
        type(self).calls += 1
        return [{"title": "Firma s.r.o.", "href": "https://firma.sk/", "body": ""}]


def _patch_import(monkeypatch, ddgs_cls):
    ddgs_cls.calls = 0
    fake_module = SimpleNamespace(DDGS=ddgs_cls)
    monkeypatch.setattr(
        website_finder,
        "importlib",
        SimpleNamespace(import_module=lambda _name: fake_module),
    )


def test_breaker_starts_off():
    assert _ddg_is_disabled() is False


def test_first_failure_trips_breaker_and_warns(monkeypatch, caplog):
    _patch_import(monkeypatch, _BoomDDGS)
    finder = WebsiteFinder()

    with caplog.at_level("WARNING"):
        assert finder._search('"Firma s.r.o."') == []

    assert _ddg_is_disabled() is True
    assert "DuckDuckGo unreachable" in caplog.text


def test_later_calls_short_circuit_without_network(monkeypatch):
    _patch_import(monkeypatch, _BoomDDGS)
    finder = WebsiteFinder()

    finder._search('"Firma s.r.o."')
    assert _BoomDDGS.calls == 1

    # Dalsie query uz nesmu ani zavolat DDGS.
    assert finder._search('"Druha firma s.r.o."') == []
    assert _BoomDDGS.calls == 1


def test_later_calls_log_at_debug_only(monkeypatch, caplog):
    _patch_import(monkeypatch, _BoomDDGS)
    finder = WebsiteFinder()
    finder._search('"Firma s.r.o."')

    with caplog.at_level("DEBUG"):
        finder._search('"Firma s.r.o."')

    debug_lines = [r for r in caplog.records if r.levelname == "DEBUG"]
    assert any("DDG disabled" in r.message for r in debug_lines)

    warn_lines = [r for r in caplog.records if r.levelname == "WARNING"]
    # Iba jediny WARNING z prveho zlyhania.
    assert len([r for r in warn_lines if "DuckDuckGo unreachable" in r.message]) == 1


async def test_find_website_skips_all_queries_when_disabled(monkeypatch):
    _patch_import(monkeypatch, _BoomDDGS)
    finder = WebsiteFinder()

    # Prvy beh: prva query zlyha a breaker sa zapne.
    await finder.find_website(company_name="Firma s.r.o.", ico="12345678")
    assert _BoomDDGS.calls == 1

    # Druha firma: ziadny dalsi sietovy pokus.
    result = await finder.find_website(
        company_name="Druha Firma s.r.o.",
        city="Bratislava",
        ico="87654321",
    )

    assert result is None
    assert _BoomDDGS.calls == 1


def test_success_does_not_trip_breaker(monkeypatch):
    _patch_import(monkeypatch, _OkDDGS)
    finder = WebsiteFinder()

    results = finder._search('"Firma s.r.o."')

    assert len(results) == 1
    assert _ddg_is_disabled() is False
