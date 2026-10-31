import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.shared.infrastructure.db.base import Base


class BillingPaymentOrderModel(Base):
    """Server-owned payment intent and exactly-once entitlement record."""

    __tablename__ = "billing_payment_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_ref = Column(String(40), nullable=False, unique=True)
    provider = Column(String(16), nullable=False)
    provider_ref = Column(String(128), nullable=True, unique=True)
    user_id = Column(String(36), nullable=False)
    company_id = Column(String(36), nullable=False, index=True)
    listing_id = Column(String(36), nullable=True)
    product_kind = Column(String(24), nullable=False)
    tier = Column(String(24), nullable=False)
    duration_days = Column(Integer, nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    status = Column(String(16), nullable=False, default="pending", index=True)
    stripe_subscription_id = Column(String(128), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
