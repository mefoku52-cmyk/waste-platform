"""Prediction API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.modules.prediction.application.factory import (
    create_prediction_service,
    create_prediction_service_with_db,
)
from app.modules.prediction.domain.types import PredictionRequest
from app.modules.prediction.presentation.schemas import (
    PredictionAccessResponse,
    PredictionRequestSchema,
    PredictionResultResponse,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import current_user_id
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/prediction", tags=["prediction"])


def _service_for(session):
    try:
        return create_prediction_service_with_db(session=session)
    except Exception:
        return create_prediction_service()


def _access_status(access) -> str:
    if not access.service_enabled:
        return "disabled"
    if not access.entitled:
        return "not_entitled"
    if not access.provider_available:
        return "unavailable"
    return "active"


@router.get(
    "/access",
    response_model=PredictionAccessResponse,
    responses=error_responses(401, 500),
)
async def get_prediction_access(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> PredictionAccessResponse:
    principal_id = current_user_id(current_user)
    if not principal_id:
        raise HTTPException(status_code=401, detail="Missing user id")

    service = _service_for(session)
    access = await service.access(principal_id=principal_id)
    return PredictionAccessResponse(
        serviceEnabled=access.service_enabled,
        entitled=access.entitled,
        providerAvailable=access.provider_available,
        status=_access_status(access),
    )


@router.post(
    "/predict",
    response_model=PredictionResultResponse,
    responses=error_responses(401, 422, 500),
)
async def predict(
    payload: PredictionRequestSchema,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> PredictionResultResponse:
    principal_id = current_user_id(current_user)
    if not principal_id:
        raise HTTPException(status_code=401, detail="Missing user id")

    service = _service_for(session)
    result = await service.predict(
        principal_id=principal_id,
        request=PredictionRequest(
            subject_type=payload.subjectType,
            subject_id=payload.subjectId,
            context=payload.context,
        ),
    )
    return PredictionResultResponse(
        status=result.status.value,
        score=result.score,
        confidence=result.confidence,
        factors=list(result.factors),
        provider=result.provider,
        metadata=result.metadata,
    )
