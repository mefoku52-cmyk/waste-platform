import json
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user

from ..infrastructure.models import TransportOffer
from .schemas import TransportOfferCreateRequest, TransportOfferResponse

router = APIRouter(prefix="/transport", tags=["transport"])


@router.post("/offers", response_model=TransportOfferResponse, status_code=201)
async def create_transport_offer(
    payload: TransportOfferCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_current_user),
):

    from datetime import datetime

    now = datetime.now()

    # Vytvoríme nový záznam
    offer = TransportOffer(
        id=uuid.uuid4(),
        company_id=str(payload.companyId),
        title=payload.title,
        description=payload.description,
        transport_from=payload.transportFrom,
        transport_to=payload.transportTo,
        vehicle_type=payload.vehicleType,
        capacity_tons=payload.capacityTons,
        price_per_km=payload.pricePerKm,
        currency=payload.currency,
        has_refrigeration=payload.hasRefrigeration,
        has_adr=payload.hasAdr,
        has_hydraulic_arm=payload.hasHydraulicArm,
        hazardous_types=json.dumps(payload.hazardousTypes),
        status="active",
        created_at=now,
        updated_at=now,
    )

    session.add(offer)
    await session.commit()
    await session.refresh(offer)

    return TransportOfferResponse(
        id=offer.id,
        title=offer.title,
        description=offer.description,
        transportFrom=offer.transport_from,
        transportTo=offer.transport_to,
        vehicleType=offer.vehicle_type,
        capacityTons=offer.capacity_tons,
        pricePerKm=offer.price_per_km,
        currency=offer.currency,
        hasRefrigeration=offer.has_refrigeration,
        hasAdr=offer.has_adr,
        hasHydraulicArm=offer.has_hydraulic_arm,
        hazardousTypes=json.loads(offer.hazardous_types) if offer.hazardous_types else [],
        status=offer.status,
        createdAt=offer.created_at,
    )


@router.get("/offers", response_model=list[TransportOfferResponse])
async def list_transport_offers(
    company_id: uuid.UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    query = select(TransportOffer).where(TransportOffer.status == "active")
    if company_id:
        query = query.where(TransportOffer.company_id == company_id)

    result = await session.execute(query)
    offers = result.scalars().all()

    return [
        TransportOfferResponse(
            id=o.id,
            title=o.title,
            description=o.description,
            transportFrom=o.transport_from,
            transportTo=o.transport_to,
            vehicleType=o.vehicle_type,
            capacityTons=o.capacity_tons,
            pricePerKm=o.price_per_km,
            currency=o.currency,
            hasRefrigeration=o.has_refrigeration,
            hasAdr=o.has_adr,
            hasHydraulicArm=o.has_hydraulic_arm,
            status=o.status,
            createdAt=o.created_at,
        )
        for o in offers
    ]
