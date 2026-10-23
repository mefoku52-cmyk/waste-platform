import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class TransportOffer(Base):
    __tablename__ = "transport_offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Odkiaľ - Kam
    transport_from = Column(String(255), nullable=False)
    transport_to = Column(String(255), nullable=True)  # Ak je null, tak "kamkoľvek"

    # Typ vozidla a kapacita
    vehicle_type = Column(String(120), nullable=False)  # kamión, dodávka, hydraulická ruka
    capacity_tons = Column(Float, nullable=True)

    # Cena
    price_per_km = Column(Float, nullable=True)
    currency = Column(String(8), nullable=False, default="EUR")

    # Špeciálne vlastnosti
    has_refrigeration = Column(Boolean, nullable=False, default=False)
    has_adr = Column(Boolean, nullable=False, default=False)
    has_hydraulic_arm = Column(Boolean, nullable=False, default=False)

    # Stav a audit
    status = Column(String(32), nullable=False, default="active")  # active, inactive
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
