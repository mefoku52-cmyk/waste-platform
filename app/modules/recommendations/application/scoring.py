"""Deterministic scoring for recommendation candidates. No I/O."""


def score_company(
    *, listing_location: str, city: str | None, logistics_capability: bool
) -> tuple[int, list[str]]:
    score = 40
    reasons = ["verified_buyer"]

    location = (listing_location or "").casefold()
    city_norm = (city or "").strip().casefold()
    if city_norm and city_norm in location:
        score += 20
        reasons.append("city_in_listing_location")

    if logistics_capability:
        score += 10
        reasons.append("logistics_capability")

    return score, reasons
