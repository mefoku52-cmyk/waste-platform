from app.modules.recommendations.application.material_taxonomy import expand_material
from app.modules.recommendations.application.scoring import (
    score_company,
    score_company_batch,
)


def _score(material: str, accepted: str | None) -> tuple[int, list[str]]:
    return score_company(
        listing_location="Zemplin",
        listing_material=material,
        listing_lat=None,
        listing_lng=None,
        city="Zilina",
        logistics_capability=False,
        accepted_material_types=accepted,
        company_lat=None,
        company_lng=None,
    )


def test_aliases_and_ewc():
    assert "bio" in expand_material("kompost")
    assert "drevo" in expand_material("piliny")
    assert "kov" in expand_material("17 04 05")


def test_match_and_mismatch():
    score, reasons = _score("Bio", "kompost")
    assert score == 80
    assert "material_accepted" in reasons
    score, reasons = _score("Železo kov", "pet")
    assert score == 0
    assert reasons == ["material_mismatch"]
    score, reasons = _score("PET", None)
    assert score == 40


def test_compact_ewc_metal_not_construction():
    assert "kov" in expand_material("170405")
    assert "kov" in expand_material("17-04-05")
    assert "stavebne" not in expand_material("170405")
    assert "stavebne" in expand_material("170101")


def test_fuzzy_edge_cases():
    assert expand_material("") == set()
    assert expand_material(None) == set()
    assert "kov" in expand_material("  17 04 05  ")
    assert "kov" in expand_material("17.04.05")
    assert "sklo" in expand_material("150107")
    assert "eeo" in expand_material("elektroodpad")
    assert "bio" in expand_material("Bio, kompost")
    unknown = expand_material("xyzzy")
    assert "xyzzy" in unknown
    assert "kov" not in unknown


def test_bio_waste_and_hazardous():
    assert "bio" in expand_material("biowaste")
    assert "bio" in expand_material("200108")
    assert "bio" in expand_material("20 01 08")
    assert "hazardous" in expand_material("13 02 05")
    assert "hazardous" in expand_material("160213")
    assert "hazardous" not in expand_material("170405")


def test_expand_material_cache_returns_independent_sets():
    first = expand_material("PET")
    first.add("cache_poison")

    second = expand_material("PET")

    assert isinstance(second, set)
    assert "cache_poison" not in second
    assert "pet" in second


def test_expand_material_cache_normalizes_equivalent_ewc_inputs():
    assert expand_material("17-04-05") == expand_material("17 04 05")


def test_score_company_batch_parity_with_score_company():
    rows = [
        {
            "listing_location": "Bratislava",
            "listing_material": "ocel",
            "listing_lat": None,
            "listing_lng": None,
            "city": "Bratislava",
            "logistics_capability": False,
            "event_hits": 0,
            "accepted_material_types": "ocel",
            "company_lat": None,
            "company_lng": None,
        },
        {
            "listing_location": "Kosice",
            "listing_material": "drevo",
            "listing_lat": None,
            "listing_lng": None,
            "city": "Bratislava",
            "logistics_capability": True,
            "event_hits": 3,
            "accepted_material_types": "ocel",
            "company_lat": None,
            "company_lng": None,
        },
        {
            "listing_location": "",
            "listing_material": "pet",
            "listing_lat": 48.1486,
            "listing_lng": 17.1077,
            "city": None,
            "logistics_capability": False,
            "event_hits": 0,
            "accepted_material_types": None,
            "company_lat": 48.1486,
            "company_lng": 17.1077,
        },
    ]
    batch_results = score_company_batch(rows)
    single_results = [
        score_company(
            listing_location=r["listing_location"],
            listing_material=r["listing_material"],
            listing_lat=r["listing_lat"],
            listing_lng=r["listing_lng"],
            city=r["city"],
            logistics_capability=r["logistics_capability"],
            event_hits=r["event_hits"],
            accepted_material_types=r["accepted_material_types"],
            company_lat=r["company_lat"],
            company_lng=r["company_lng"],
        )
        for r in rows
    ]
    assert batch_results == single_results


def test_score_company_batch_empty():
    assert score_company_batch([]) == []


def test_scoring_cache_reuse_and_bounded_size():
    from app.modules.recommendations.application import scoring as scoring_mod

    # Vyčisti cache pred testom (deterministicky inicialny stav).
    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()

    info_before = scoring_mod._material_compat_cached.cache_info()
    assert info_before.hits == 0 and info_before.currsize == 0

    # Opakovane volanie so vzdy tymi istymi argumentmi -> cache hits.
    score_company(
        listing_location="Bratislava",
        listing_material="ocel",
        listing_lat=None,
        listing_lng=None,
        city="Bratislava",
        logistics_capability=False,
        event_hits=0,
        accepted_material_types="ocel",
        company_lat=None,
        company_lng=None,
    )
    score_company(
        listing_location="Bratislava",
        listing_material="ocel",
        listing_lat=None,
        listing_lng=None,
        city="Bratislava",
        logistics_capability=False,
        event_hits=0,
        accepted_material_types="ocel",
        company_lat=None,
        company_lng=None,
    )

    info_after = scoring_mod._material_compat_cached.cache_info()
    assert info_after.hits >= 1
    assert info_after.maxsize is not None
    assert info_after.currsize <= info_after.maxsize

    # Napln cache nad maxsize a over, ze ostala obmedzena (evikcia funguje).
    cache_maxsize = scoring_mod._material_compat_cached.cache_info().maxsize
    assert cache_maxsize is not None
    for i in range(cache_maxsize + 50):
        scoring_mod._material_compat_cached(f"accepted_{i}", f"offered_{i}")
    info_big = scoring_mod._material_compat_cached.cache_info()
    assert info_big.maxsize is not None
    assert info_big.currsize <= info_big.maxsize

    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()


def test_scoring_cache_deterministic_results():
    from app.modules.recommendations.application import scoring as scoring_mod

    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()

    args = ("Bratislava", "Kosice centrum")
    r1 = scoring_mod._city_match_cached(*args)
    r2 = scoring_mod._city_match_cached(*args)
    assert r1 == r2

    m1 = scoring_mod._material_compat_cached("ocel", "ocel")
    m2 = scoring_mod._material_compat_cached("ocel", "ocel")
    assert m1 == m2 == 1

    scoring_mod._material_compat_cached.cache_clear()
    scoring_mod._city_match_cached.cache_clear()
