from pathlib import Path

from bs4 import BeautifulSoup

from app.modules.lead_finder.application.services.directory_lookup import (
    _extract_card_website,
    _extract_joomla_cloak_email,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "directory"


def _load_card(name: str):
    """Parse a captured Zlaté stránky card fixture into its card element."""
    html = (_FIXTURE_DIR / name).read_text(encoding="utf-8")
    cards = BeautifulSoup(html, "html.parser").select("div.profile-holder")

    assert cards, f"fixture {name} contains no profile-holder card"

    return cards[0]


def test_extract_joomla_cloak_email_simple():
    html = """
    <script>
    var addy123 = 'john' + '&#64;' + 'firma' + '&#46;' + 'sk';
    </script>
    """

    assert _extract_joomla_cloak_email(html) == "john@firma.sk"


def test_extract_joomla_cloak_email_real_odpady_tatry_pattern():
    html = """
    <script>
    var addye6f0620f845c3f2a783276ad01d35c01 =
        '&#111;dp&#97;dyt&#97;try' + '&#64;';

    addye6f0620f845c3f2a783276ad01d35c01 =
        addye6f0620f845c3f2a783276ad01d35c01
        + 'gm&#97;&#105;l'
        + '&#46;'
        + 'c&#111;m';
    </script>
    """

    assert _extract_joomla_cloak_email(html) == "odpadytatry@gmail.com"


def test_extract_joomla_cloak_email_rejects_junk_email():
    html = """
    <script>
    var addy123 = 'noreply' + '&#64;' + 'example' + '&#46;' + 'com';
    </script>
    """

    assert _extract_joomla_cloak_email(html) is None


def test_extract_joomla_cloak_email_ignores_invalid_expression():
    html = """
    <script>
    var addy123 = unknown_value + '&#64;' + 'example' + '&#46;' + 'com';
    </script>
    """

    assert _extract_joomla_cloak_email(html) is None


def _profile_html(mailto: str) -> str:
    # A matching Zlaté stránky profile card: the /firmy/... anchor is what
    # _extract_card_name uses to derive the card name that must match.
    return f"""
    <html><body>
      <div class="profile-holder">
        <a href="/firmy/kosice/H1234567890/">EKOL - recyklacne systemy s.r.o.</a>
        <a href="mailto:{mailto}">email</a>
      </div>
    </body></html>
    """


def test_directory_lookup_rejects_non_matching_consumer_email(monkeypatch):
    """D2: consumer mailbox, ktorej local-part nesedi s nazvom firmy,
    sa nadalej nesmie dostat cez mailto vetvu.

    (Pozor: od zavedenia D2 sa free provider s *zhodnym* local-partom
    PRIJIMA — vid test nizsie. Tento test pokryva nezhodny pripad.)
    """
    from app.modules.lead_finder.application.services import directory_lookup

    class FakeResp:
        status_code = 200
        text = _profile_html("jan.novak@mail.t-com.sk")

    monkeypatch.setattr(directory_lookup.httpx, "get", lambda *a, **kw: FakeResp())

    result = directory_lookup.lookup_public_email(
        company_name="EKOL - recyklacne systemy s.r.o.",
        city="Kosice",
        ico="36507440",
    )
    assert result is None


def test_extract_card_email_accepts_gmail_when_local_matches():
    """D2: mikrofirmy komunikuju cez Gmail; adresa prejde, ak local-part
    obsahuje aspon 3 znaky z normalizovaneho nazvu firmy."""
    from app.modules.lead_finder.application.services.directory_lookup import (
        _extract_card_email,
    )

    html = """
    <html><body>
      <div class="profile-holder">
        <a href="/firmy/Poprad/H1234567890/">ODPADY TATRY, s. r. o.</a>
        <a href="mailto:odpadytatry@gmail.com">email</a>
      </div>
    </body></html>
    """

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert _extract_card_email(card, "ODPADY TATRY, s. r. o.") == "odpadytatry@gmail.com"


def test_extract_card_email_rejects_gmail_when_local_does_not_match():
    """D2: Gmail od cudzej osoby (jan.novak) neprejde."""
    from app.modules.lead_finder.application.services.directory_lookup import (
        _extract_card_email,
    )

    html = """
    <html><body>
      <div class="profile-holder">
        <a href="/firmy/Poprad/H1234567890/">ODPADY TATRY, s. r. o.</a>
        <a href="mailto:jan.novak@gmail.com">email</a>
      </div>
    </body></html>
    """

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert _extract_card_email(card, "ODPADY TATRY, s. r. o.") is None


def test_extract_card_email_without_company_name_stays_strict():
    """Bez nazvu firmy sa neda overit D2 → free provider sa zahodi."""
    from app.modules.lead_finder.application.services.directory_lookup import (
        _extract_card_email,
    )

    html = """
    <html><body>
      <div class="profile-holder">
        <a href="/firmy/Poprad/H1234567890/">ODPADY TATRY, s. r. o.</a>
        <a href="mailto:odpadytatry@gmail.com">email</a>
      </div>
    </body></html>
    """

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert _extract_card_email(card) is None


def test_directory_lookup_accepts_business_email(monkeypatch):
    """Kontrola: firemna domena (nie consumer) prejde cez mailto vetvu."""
    from app.modules.lead_finder.application.services import directory_lookup

    class FakeResp:
        status_code = 200
        text = _profile_html("info@ekolpresov.sk")

    monkeypatch.setattr(directory_lookup.httpx, "get", lambda *a, **kw: FakeResp())

    result = directory_lookup.lookup_public_email(
        company_name="EKOL - recyklacne systemy s.r.o.",
        city="Kosice",
        ico="36507440",
    )
    assert result == "info@ekolpresov.sk"


def test_extract_card_website_prefers_homepage_over_register():
    """Regresia: karta s homepage aj registrom musi vratit homepage.

    Stara logika brala PRVY externy link; na realnych kartach by vsak
    indexpodnikatela.sk mohol vyhrat. Fix cita dedikovany `li.link` slot.
    """
    card = _load_card("ekol_card.html")

    result = _extract_card_website(card)

    assert result == "https://www.ekolpresov.sk"
    assert "indexpodnikatela.sk" not in result


def test_extract_card_website_returns_none_when_only_register_link():
    """Karta bez homepage nesmie vratit registrovu URL.

    3 z 9 realnych kariet maju ako jediny externy link indexpodnikatela.sk.
    Vratit ju by znamenalo crawlovat obchodny register namiesto firmy.
    """
    card = _load_card("register_only_card.html")

    assert _extract_card_website(card) is None


def test_extract_card_website_falls_back_to_microdata():
    """Fallback: ak `li.link` chyba, pouzi microdata span[itemprop=url]."""
    html = """
    <html><body>
      <div class="profile-holder">
        <h1 itemprop="name">
          <a href="/firmy/Presov/H1012003/EKOL+RECYKLACNE+SYSTEMY+s.r.o./">EKOL s.r.o.</a>
        </h1>
        <a href="https://www.ekolpresov.sk" target="_blank">
            <span itemprop="url">https://www.ekolpresov.sk</span>
        </a>
        <a href="https://www.indexpodnikatela.sk/36507440" target="_blank">Ekonomicke zaznamy</a>
      </div>
    </body></html>
    """

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert _extract_card_website(card) == "https://www.ekolpresov.sk"


def test_extract_card_website_ignores_zlatestranky_internal_links():
    """Interny odkaz na zlatestranky nesmie byt povazovany za firemnu stranku."""
    html = """
    <html><body>
      <div class="profile-holder">
        <li class="link"><a href="https://www.zlatestranky.sk/firmy/Presov/H1/EKOL/">profil</a></li>
      </div>
    </body></html>
    """

    card = BeautifulSoup(html, "html.parser").select("div.profile-holder")[0]

    assert _extract_card_website(card) is None
