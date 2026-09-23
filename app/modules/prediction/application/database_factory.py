from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.prediction.application.database_extractor import (
    DatabaseFeatureExtractor,
)
from app.modules.prediction.application.features import FeatureEngine
from app.modules.prediction.infrastructure.database_repository import (
    PredictionDataRepository,
)


def create_database_feature_engine(
    session: AsyncSession,
) -> FeatureEngine:
    """
    Create the real CMEP database-backed FeatureEngine.

    No DB connection is created here. The existing CMEP request/session
    lifecycle supplies the AsyncSession.
    """

    repository = PredictionDataRepository(session)

    extractor = DatabaseFeatureExtractor(repository)

    return FeatureEngine(extractor)
