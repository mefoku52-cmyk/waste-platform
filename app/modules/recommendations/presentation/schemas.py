"""recommendations API schemas."""

from uuid import UUID

from pydantic import BaseModel


class RecommendationCandidate(BaseModel):
    companyId: UUID
    legalName: str
    city: str
    countryCode: str
    buyerCapability: bool
    logisticsCapability: bool
    score: int
    reasons: list[str]

    rule_score: float | None = None
    prediction_score: float | None = None
    prediction_status: str | None = None
    prediction_applied: bool | None = None


class RecommendationsResponse(BaseModel):
    listingId: UUID
    materialType: str
    location: str
    items: list[RecommendationCandidate]
