"""Deterministic scoring for recommendation candidates. No I/O."""

from math import asin, cos, radians, sin, sqrt

from app.modules.recommendations.application.material_taxonomy import expand_material

# Interné cache pre opakovane sa vyskytujuce vstupy (optimalizacia A + C).
# Drzia sa na urovni modulu, teda pretrvavaju naprieč volaniami v rameni jednej davky
# (napr. matching_job.py prechadza firmy x ponuky, kde sa materiály a mesta opakuju).
_material_compat_cache: dict[tuple[str, str], int] = {}
# -1 = material_mismatch, 1 = material_accepted, 0 = ziadne informacie o materiale

_city_match_cache: dict[tuple[str, str], bool] = {}


def _material_compat_cached(
    accepted_text: str | None, offered_text: str | None
) -> int:
    """Vrati -1 (mismatch), 1 (accepted), 0 (ziadne) s predpoctanim pre unikatne pary."""
    key = (accepted_text or "", offered_text or "")
    cached = _material_compat_cache.get(key)
    if cached is not None:
        return cached
    accepted = expand_material(accepted_text)
    offered = expand_material(offered_text)
    if accepted and offered and accepted.isdisjoint(offered):
        result = -1
    elif accepted and offered:
        result = 1
    else:
        result = 0
    _material_compat_cache[key] = result
    return result


def _city_match_cached(city: str | None, location: str | None) -> bool:
    """Vrati ci je mesto obsahované v lokácii (casefold), s predpočítaním."""
    key = ((city or "").strip(), location or "")
    cached = _city_match_cache.get(key)
    if cached is not None:
        return cached
    c = key[0]
    loc = key[1]
    result = bool(c and c.casefold() in loc.casefold())
    _city_match_cache[key] = result
    return result


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def score_company(
    *,
    listing_location: str,
    listing_material: str,
    listing_lat: float | None,
    listing_lng: float | None,
    city: str | None,
    logistics_capability: bool,
    event_hits: int = 0,
    accepted_material_types: str | None,
    company_lat: float | None,
    company_lng: float | None,
) -> tuple[int, list[str]]:
    listing_location = listing_location or ""
    listing_material = listing_material or ""
    city = city or ""
    accepted_material_types = accepted_material_types or None

    score = 40
    reasons = ["verified_buyer"]
    if _city_match_cached(city, listing_location):
        score += 20
        reasons.append("city_in_listing_location")

    compat = _material_compat_cached(accepted_material_types, listing_material)
    if compat == -1:
        return 0, ["material_mismatch"]
    if compat == 1:
        score += 40
        reasons.append("material_accepted")

    coords = (listing_lat, listing_lng, company_lat, company_lng)
    if all(value is not None for value in coords):
        distance_km = _distance_km(listing_lat, listing_lng, company_lat, company_lng)
        if distance_km <= 50:
            score += 20
            reasons.append("distance_le_50km")
        elif distance_km <= 150:
            score += 10
            reasons.append("distance_le_150km")

    if logistics_capability:
        score += 10
        reasons.append("logistics_capability")
    hits = max(0, int(event_hits or 0))
    if hits:
        score += min(15, hits * 5)
        reasons.append("listing_interest")
    return score, reasons


def score_company_batch(
    rows: list[dict],
) -> list[tuple[int, list[str]]]:
    """Skóruje viac (listing, company) riadkov v jednom prechode.

    Každý riadok má kľúče zodpovedajúcí menovaným parametrom score_company().
    Využíva rovnaké interné cache (_material_compat_cache, _city_match_cache),
    teda opakovane sa vyskytujuce materiálne páry a mestá sa pocitaju len raz.
    Verejné API score_company() zostáva nezmenene.
    """
    results: list[tuple[int, list[str]]] = []
    results_append = results.append
    for r in rows:
        results_append(
            score_company(
                listing_location=r.get("listing_location", ""),
                listing_material=r.get("listing_material", ""),
                listing_lat=r.get("listing_lat"),
                listing_lng=r.get("listing_lng"),
                city=r.get("city"),
                logistics_capability=r.get("logistics_capability", False),
                event_hits=r.get("event_hits", 0),
                accepted_material_types=r.get("accepted_material_types"),
                company_lat=r.get("company_lat"),
                company_lng=r.get("company_lng"),
            )
        )
    return results
