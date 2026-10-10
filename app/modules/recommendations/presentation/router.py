from app.modules.recommendations.application.routing import calculate_route

"""recommendations API router."""

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.recommendations.application.service import RecommendationsService
from app.modules.recommendations.presentation.schemas import (
    RecommendationCandidate,
    RecommendationsResponse,
)
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
    membership_company_ids,
)
from app.shared.presentation.error_schemas import error_responses

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get(
    "/listings/{listing_id}",
    response_model=RecommendationsResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def get_listing_recommendations(
    listing_id: UUID,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    service = RecommendationsService(session)
    try:
        listing = await service._get_listing(listing_id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not is_platform_admin(current_user):
        allowed = {str(cid) for cid in membership_company_ids(current_user)}
        if str(listing.company_id) not in allowed:
            raise HTTPException(status_code=403, detail="Not allowed to view recommendations")

    payload = await service.list_for_listing(listing_id)

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="recommendation_generated",
        target_type="listing",
        target_id=listing_id,
        details=f"candidates={len(payload['items'])}",
    )

    return RecommendationsResponse(
        listingId=payload["listingId"],
        materialType=payload["materialType"],
        location=payload["location"],
        items=[RecommendationCandidate(**item) for item in payload["items"]],
    )


@router.get("/route")
async def get_route(
    origin: str = Query(...),
    destination: str = Query(...),
    consumption: float = Query(28.0),
    fuel_price: float = Query(1.49),
    roundtrip: bool = Query(False),
    current_user: object = Depends(require_current_user),
) -> dict:
    del current_user
    try:
        return await asyncio.to_thread(
            calculate_route,
            origin_text=origin,
            destination_text=destination,
            consumption=consumption,
            fuel_price=fuel_price,
            roundtrip=roundtrip,
        )
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/carriers")
async def get_carriers(
    near: str = Query(...),
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> dict:
    del current_user
    service = RecommendationsService(session)
    items = await service.logistics_candidates(near)
    return {"near": near, "items": items, "source": "companies"}
