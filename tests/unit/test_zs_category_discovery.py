"""Tests for category-based Zlaté stránky discovery."""

from bs4 import BeautifulSoup

from app.modules.lead_finder.application.services import zs_category_discovery as zs


def _card(
    mailto: str = "",
    profile: str = "/firmy/Kosice/H1234567890/Firma+s.r.o./",
    name: str = "Firma s.r.o.",
    tel: str | None = None,
    web: str | None = None,
) -> str:
    parts = [f'<a href="{profile}">{name}</a>']

    if mailto:
        parts.append(f'<a href="mailto:{mailto}">email</a>')
    if tel:
        parts.append(f'<a href="tel:{tel}">tel</a>')
    if web:
        parts.append(f'<li class="link"><a href="{web}">web</a></li>')

    return f'<div class="profile-holder">{"".join(parts)}</div>'


def _parse(html: str):
    return BeautifulSoup(html, "html.parser").select("div.profile-holder")


def test_category_url_encodes_slug():
    assert (
        zs._category_url("kovový odpad", 2)
        == "https://www.zlatestranky.sk/firmy/-/q_kovov%C3%BD%20odpad/2/"
    )


def test_extract_card_phone_from_tel_href():
    card = _parse(_card(tel="+421903427162"))[0]

    assert zs._extract_card_phone(card) == "+421903427162"


def test_extract_card_location_from_profile_link():
    card = _parse(_card(profile="/firmy/Bratislava/H1640949/X/"))[0]

    city, profile_url = zs._extract_card_location(card)

    assert city == "Bratislava"
    assert profile_url == "https://www.zlatestranky.sk/firmy/Bratislava/H1640949/X/"


def test_extract_card_data_returns_none_without_email():
    card = _parse(_card())[0]

    assert zs._extract_card_data(card) is None


def test_extract_card_data_returns_none_without_name():
    html = '<div class="profile-holder"><a href="mailto:info@firma.sk">e</a></div>'

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert zs._extract_card_data(card) is None


def test_extract_card_data_reads_full_record():
    card = _parse(
        _card(
            mailto="info@firma.sk",
            tel="+421900111222",
            web="https://firma.sk",
        )
    )[0]

    company = zs._extract_card_data(card)

    assert company is not None
    assert company.company_name == "Firma s.r.o."
    assert company.email == "info@firma.sk"
    assert company.phone == "+421900111222"
    assert company.website == "https://firma.sk"
    assert company.city == "Kosice"
    assert company.source_url.startswith("https://www.zlatestranky.sk/firmy/Kosice/")


def test_discover_from_category_dedupes_by_email(monkeypatch):
    pages = {
        1: _card(mailto="info@firma.sk"),
        # Rovnaká firma znova + jedna nová: duplicita sa musí zlúčiť.
        2: _card(mailto="info@firma.sk")
        + _card(
            mailto="druha@firma2.sk",
            profile="/firmy/Trnava/H9999999999/Druha+s.r.o./",
            name="Druha s.r.o.",
        ),
    }

    def fake_get(url: str) -> str:
        for page, html in pages.items():
            if url.endswith(f"/{page}/"):
                return html
        return ""

    monkeypatch.setattr(zs, "_get", fake_get)
    monkeypatch.setattr(zs.time, "sleep", lambda _seconds: None)

    result = zs.discover_from_category("odpady", max_pages=2)

    assert len(result) == 2
    assert {c.email for c in result} == {"info@firma.sk", "druha@firma2.sk"}


def test_discover_from_category_stops_on_empty_page(monkeypatch):
    def fake_get(url: str) -> str:
        return _card(mailto="info@firma.sk") if url.endswith("/1/") else ""

    monkeypatch.setattr(zs, "_get", fake_get)
    monkeypatch.setattr(zs.time, "sleep", lambda _seconds: None)

    assert len(zs.discover_from_category("odpady", max_pages=5)) == 1


def test_discover_from_category_empty_slug():
    assert zs.discover_from_category("") == []
