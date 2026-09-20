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


class RecommendationsResponse(BaseModel):
    listingId: UUID
    materialType: str
    location: str
    items: list[RecommendationCandidate]
