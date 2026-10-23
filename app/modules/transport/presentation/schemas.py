from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TransportOfferCreateRequest(BaseModel):
    title: str
    description: str | None = None
    transportFrom: str
    transportTo: str | None = None
    vehicleType: str
    capacityTons: float | None = None
    pricePerKm: float | None = None
    currency: str = "EUR"
    hasRefrigeration: bool = False
    hasAdr: bool = False
    hasHydraulicArm: bool = False
    companyId: UUID


class TransportOfferResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    transportFrom: str
    transportTo: str | None
    vehicleType: str
    capacityTons: float | None
    pricePerKm: float | None
    currency: str
    hasRefrigeration: bool
    hasAdr: bool
    hasHydraulicArm: bool
    status: str
    createdAt: datetime
