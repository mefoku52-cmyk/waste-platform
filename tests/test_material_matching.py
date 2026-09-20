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
