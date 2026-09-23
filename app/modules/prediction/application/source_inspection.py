from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.prediction.infrastructure.database_repository import (
    PredictionDataRepository,
)

PREDICTION_SOURCE_TABLES = (
    "listings",
    "listing_views",
    "inquiries",
    "recommendations",
    "recommendation_results",
    "listing_recommendations",
    "activity_events",
    "events",
    "analytics_events",
)


async def inspect_prediction_sources(
    session: AsyncSession,
) -> dict[str, bool]:
    """
    Read-only inspection of prediction-relevant database sources.
    """

    repository = PredictionDataRepository(session)

    return await repository.available_tables(PREDICTION_SOURCE_TABLES)
