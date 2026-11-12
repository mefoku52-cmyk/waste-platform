"""inspections dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import InspectionService
from ..infrastructure.repositories import (
    InspectionEventRepositoryImpl,
    InspectionRepositoryImpl,
)
from ..infrastructure.streaming_client import get_streaming_client


def get_inspection_service(session: AsyncSession = Depends(get_db_session)) -> InspectionService:
    return InspectionService(
        session,
        InspectionRepositoryImpl(session),
        InspectionEventRepositoryImpl(session),
        get_streaming_client(),
    )
