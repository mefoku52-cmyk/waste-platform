from app.modules.recommendations.application.material_taxonomy import expand_material
from app.modules.recommendations.application.scoring import score_company


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
