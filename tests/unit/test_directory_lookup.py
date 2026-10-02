from app.modules.lead_finder.application.services.directory_lookup import (
    _extract_joomla_cloak_email,
)


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


def test_directory_lookup_rejects_consumer_emails(monkeypatch):
    """Slovak Telekom / O2 / Orange consumer mails sa nesmu
    dostat cez mailto vetvu."""
    from app.modules.lead_finder.application.services import directory_lookup

    class FakeResp:
        status_code = 200
        text = _profile_html("ekolpresov@mail.t-com.sk")

    monkeypatch.setattr(directory_lookup.httpx, "get", lambda *a, **kw: FakeResp())

    result = directory_lookup.lookup_public_email(
        company_name="EKOL - recyklacne systemy s.r.o.",
        city="Kosice",
        ico="36507440",
    )
    assert result is None


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
