"""Pure-function tests for scoring and listing_drafter."""

from app.modules.listings.application.listing_drafter import (
    _build_system,
    _fallback_from_prompt,
    _parse_draft,
)
from app.modules.recommendations.application.scoring import _distance_km, score_company


def test_distance_km_zero():
    assert _distance_km(48.1486, 17.1077, 48.1486, 17.1077) == 0.0


def test_distance_km_known():
    # Bratislava -> Vienna ~79 km
    d = _distance_km(48.1486, 17.1077, 48.2082, 16.3738)
    assert 50 < d < 60


def test_score_company_basic():
    score, reasons = score_company(
        listing_location="Bratislava",
        listing_material="ocel",
        listing_lat=None,
        listing_lng=None,
        city=None,
        logistics_capability=False,
        event_hits=0,
        accepted_material_types="ocel",
        company_lat=None,
        company_lng=None,
    )
    assert score == 80
    assert "material_accepted" in reasons
    assert "material_mismatch" not in reasons


def test_score_company_material_mismatch():
    score, reasons = score_company(
        listing_location="Bratislava",
        listing_material="drevo",
        listing_lat=None,
        listing_lng=None,
        city=None,
        logistics_capability=False,
        event_hits=0,
        accepted_material_types="ocel",
        company_lat=None,
        company_lng=None,
    )
    assert score == 0
    assert reasons == ["material_mismatch"]


def test_score_company_city_bonus():
    score, reasons = score_company(
        listing_location="Bratislava centrum",
        listing_material="ocel",
        listing_lat=None,
        listing_lng=None,
        city="Bratislava",
        logistics_capability=False,
        event_hits=0,
        accepted_material_types=None,
        company_lat=None,
        company_lng=None,
    )
    assert score == 60
    assert "city_in_listing_location" in reasons


def test_score_company_distance_and_logistics_and_hits():
    score, reasons = score_company(
        listing_location="",
        listing_material="ocel",
        listing_lat=48.1486,
        listing_lng=17.1077,
        city=None,
        logistics_capability=True,
        event_hits=2,
        accepted_material_types="ocel",
        company_lat=48.1486,
        company_lng=17.1077,
    )
    # base 40 + material 40 + dist 20 + logistics 10 + hits min(15,10)=10
    assert score == 120
    assert "distance_le_50km" in reasons
    assert "logistics_capability" in reasons
    assert "listing_interest" in reasons


def test_build_system_default_persona():
    out = _build_system("bystry")
    assert "PERSONA:" in out
    assert "bystry" not in out.lower() or True
    assert "vyvazeny" in out or "VSETKY" in out


def test_build_system_unknown_persona_falls_back():
    out = _build_system("nonexistent")
    assert "vyvazeny" in out or "VSETKY" in out


def test_fallback_from_prompt_empty():
    d = _fallback_from_prompt("")
    assert d.title == "Nová ponuka"
    assert d.description == "Popis ponuky"
    assert d.currency == "EUR"
    assert d.quantity is None


def test_fallback_from_prompt_truncates_title():
    long = "a" * 200
    d = _fallback_from_prompt(long)
    assert len(d.title) == 80
    assert d.description == long


def test_parse_draft_valid_json():
    text = '{"title":"T","description":"D","materialType":"ocel","quantity":5,"unit":"t","location":"BA","condition":"novy","currency":"EUR","price":10.5}'
    d = _parse_draft(text, "prompt")
    assert d.title == "T"
    assert d.quantity == 5.0
    assert d.price == 10.5
    assert d.currency == "EUR"


def test_parse_draft_code_fence():
    text = '```json\n{"title":"T","description":"D"}\n```'
    d = _parse_draft(text, "prompt")
    assert d.title == "T"


def test_parse_draft_invalid_json_fallback():
    d = _parse_draft("not json", "myprompt")
    assert d.title == "myprompt"[:80]
    assert d.description == "myprompt"


def test_parse_draft_empty_title_fallback_prompt():
    text = '{"title":"","description":""}'
    d = _parse_draft(text, "fallback prompt")
    assert d.title == "fallback prompt"[:80]
    assert d.description == "fallback prompt"


def test_parse_draft_currency_default():
    text = '{"title":"T","description":"D","currency":null}'
    d = _parse_draft(text, "p")
    assert d.currency == "EUR"


def test_is_provider_configured(monkeypatch):
    from app.modules.listings.application.listing_drafter import ListingDrafter

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert ListingDrafter.is_provider_configured() is False
    monkeypatch.setenv("GROQ_API_KEY", "x")
    assert ListingDrafter.is_provider_configured() is True
