"""website_finder._is_skippable_domain + WebsiteFinder bez siet."""

import pytest

from app.modules.lead_finder.application.services.website_finder import (
    _SKIP_DOMAINS,
    WebsiteFinder,
    _is_skippable_domain,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://facebook.com/page",
        "https://www.facebook.com/x",
        "https://linkedin.com/in/x",
        "https://twitter.com/x",
        "https://youtube.com/watch?v=x",
        "https://discord.com/invite/x",
        "https://github.com/x/y",
        "https://reddit.com/r/x",
        "https://zoznam.sk/x",
        "https://finstat.sk/x",
        "https://google.com/search",
        "https://wikipedia.org/wiki/X",
        "https://bazos.sk/x",
        "https://profesia.sk/x",
        "https://hst.link/x",
    ],
)
def test_skippable_domains(url):
    assert _is_skippable_domain(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://mojafirma.sk",
        "https://drevosk.sk/kontakt",
        "https://recyklacia-firma.sk/o-nas",
        "https://ekol.sk",
        "http://www.firma.sk",
    ],
)
def test_not_skippable_domains(url):
    assert _is_skippable_domain(url) is False


def test_skippable_empty_url():
    assert _is_skippable_domain("") is True


def test_skippable_invalid_url():
    assert _is_skippable_domain("not-a-url") is True


def test_skip_domains_contains_key_platforms():
    assert "facebook.com" in _SKIP_DOMAINS
    assert "linkedin.com" in _SKIP_DOMAINS
    assert "discord.com" in _SKIP_DOMAINS
    assert "wikipedia.org" in _SKIP_DOMAINS


def test_finder_init():
    finder = WebsiteFinder()
    assert finder is not None


def test_finder_is_available():
    """V testovacom prostredi ddgs nemusi byt nainstalovany."""
    finder = WebsiteFinder()
    result = finder.is_available()
    assert isinstance(result, bool)
