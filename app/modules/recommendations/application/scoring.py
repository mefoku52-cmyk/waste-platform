"""Deterministic scoring for recommendation candidates. No I/O."""

from math import asin, cos, radians, sin, sqrt


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


MATERIAL_ALIASES = {
    "bio": {"bio", "kompost", "organic", "organicke"},
    "drevo": {"drevo", "wood", "piliny", "pilovina", "piloviny"},
    "kov": {"kov", "zelezo", "železo", "metal", "spony"},
    "pet": {"pet", "plast", "plastove", "granule"},
    "papier": {"papier", "paper", "karton"},
}


def _expand(tokens: set[str]) -> set[str]:
    out = set(tokens)
    for token in tokens:
        for group in MATERIAL_ALIASES.values():
            if token in group:
                out |= group
    return out


def _material_tokens(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {part.strip().casefold() for part in raw.replace(";", ",").split(",") if part.strip()}


def score_company(
    *,
    listing_location: str,
    listing_material: str,
    listing_lat: float | None,
    listing_lng: float | None,
    city: str | None,
    logistics_capability: bool,
    accepted_material_types: str | None,
    company_lat: float | None,
    company_lng: float | None,
) -> tuple[int, list[str]]:
    score = 40
    reasons = ["verified_buyer"]

    location = (listing_location or "").casefold()
    city_norm = (city or "").strip().casefold()
    if city_norm and city_norm in location:
        score += 20
        reasons.append("city_in_listing_location")

    accepted = _expand(_material_tokens(accepted_material_types))
    material_tokens = _expand(_material_tokens(listing_material))
    if accepted and material_tokens and accepted.isdisjoint(material_tokens):
        return 0, ["material_mismatch"]
    if accepted and material_tokens and not accepted.isdisjoint(material_tokens):
        score += 40
        reasons.append("material_accepted")

    if (
        listing_lat is not None
        and listing_lng is not None
        and company_lat is not None
        and company_lng is not None
    ):
        distance_km = _haversine_km(listing_lat, listing_lng, company_lat, company_lng)
        if distance_km <= 50:
            score += 20
            reasons.append("distance_le_50km")
        elif distance_km <= 150:
            score += 10
            reasons.append("distance_le_150km")

    if logistics_capability:
        score += 10
        reasons.append("logistics_capability")

    return score, reasons
