from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class CompanyDTO:
    id: UUID
    status: str
    legal_name: str
    trading_name: str | None
    registration_number: str
    tax_identifier: str | None
    vat_identifier: str | None
    subscription_tier: str
    company_type: str
    email: str | None
    phone: str | None
    website_url: str | None
    country_code: str
    address_line_1: str
    address_line_2: str | None
    city: str
    postal_code: str
    latitude: float | None
    longitude: float | None
    seller_capability: bool
    buyer_capability: bool
    logistics_capability: bool
    verification_submitted_at: datetime | None
    verification_reviewed_at: datetime | None
    verification_reviewed_by_user_id: UUID | None
    verified_at: datetime | None
    verified_by_user_id: UUID | None
    rejected_at: datetime | None
    rejected_by_user_id: UUID | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None
