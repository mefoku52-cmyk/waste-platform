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
