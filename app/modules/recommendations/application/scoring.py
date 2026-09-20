"""Deterministic scoring for recommendation candidates. No I/O."""

from math import asin, cos, radians, sin, sqrt

from app.modules.recommendations.application.material_taxonomy import expand_material


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
    if city.strip().casefold() and city.strip().casefold() in listing_location.casefold():
        score += 20
        reasons.append("city_in_listing_location")

    accepted = expand_material(accepted_material_types)
    offered = expand_material(listing_material)
    if accepted and offered and accepted.isdisjoint(offered):
        return 0, ["material_mismatch"]
    if accepted and offered:
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
    return score, reasons
