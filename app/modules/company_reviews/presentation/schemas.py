"""company_reviews API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.company_reviews.domain.entities import (
    MAX_BODY_LENGTH,
    MAX_RATING,
    MAX_TITLE_LENGTH,
    MIN_RATING,
)


class ReviewSubmitRequest(BaseModel):
    rating: int = Field(..., ge=MIN_RATING, le=MAX_RATING)
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    body: str | None = Field(default=None, max_length=MAX_BODY_LENGTH)


class ReviewModerateRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")


class ReviewData(BaseModel):
    id: str
    companyId: str
    authorUserId: str | None
    rating: int
    title: str | None
    body: str | None
    status: str
    moderatedAt: datetime | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class ReviewResponse(BaseModel):
    data: ReviewData


class ReviewsResponse(BaseModel):
    items: list[ReviewData]
    meta: dict


class ReviewAggregate(BaseModel):
    average: float | None
    count: int
    eligibility: dict | None = None


class ReviewAggregateResponse(BaseModel):
    data: ReviewAggregate
