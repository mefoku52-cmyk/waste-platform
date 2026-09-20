from app.modules.recommendations.application.scoring import _distance_km, score_company


def test_distance_same_point():
    assert _distance_km(48.7, 21.2, 48.7, 21.2) < 0.01


def test_distance_presov_zilina_range():
    km = _distance_km(49.0, 21.24, 49.22, 18.74)
    assert 140 < km < 220


def test_logistics_bonus():
    base = score_company(
        listing_location="Zemplin",
        listing_material="PET",
        listing_lat=None,
        listing_lng=None,
        city="Zilina",
        logistics_capability=False,
        accepted_material_types=None,
        company_lat=None,
        company_lng=None,
    )[0]
    with_log = score_company(
        listing_location="Zemplin",
        listing_material="PET",
        listing_lat=None,
        listing_lng=None,
        city="Zilina",
        logistics_capability=True,
        accepted_material_types=None,
        company_lat=None,
        company_lng=None,
    )[0]
    assert with_log - base == 10
