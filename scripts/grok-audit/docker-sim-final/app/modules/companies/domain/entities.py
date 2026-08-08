from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True)
class Company(AuditFields):
    status: CompanyStatus
    legal_name: str
    trading_name: str | None
    registration_number: str
    tax_identifier: str | None
    company_type: CompanyType
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

    def validate(self) -> None:
        if not self.legal_name:
            raise ValidationDomainError("Company legal_name is required")
        if not self.registration_number:
            raise ValidationDomainError("Company registration_number is required")
        if len(self.country_code) != 2:
            raise ValidationDomainError("Company country_code must have ISO length 2")
        if not any([self.seller_capability, self.buyer_capability, self.logistics_capability]):
            raise ValidationDomainError("At least one company capability must be enabled")

    def transition_status(self, to_status: CompanyStatus) -> None:
        allowed = {
            CompanyStatus.DRAFT: {CompanyStatus.VERIFICATION_SUBMITTED, CompanyStatus.INACTIVE},
            CompanyStatus.VERIFICATION_SUBMITTED: {CompanyStatus.VERIFIED, CompanyStatus.REJECTED, CompanyStatus.DRAFT},
            CompanyStatus.VERIFIED: {CompanyStatus.SUSPENDED, CompanyStatus.INACTIVE},
            CompanyStatus.REJECTED: {CompanyStatus.DRAFT, CompanyStatus.VERIFICATION_SUBMITTED, CompanyStatus.INACTIVE},
            CompanyStatus.SUSPENDED: {CompanyStatus.VERIFIED, CompanyStatus.INACTIVE},
            CompanyStatus.INACTIVE: set(),
        }
        ensure_transition(self.status.value, to_status.value, {s.value for s in allowed[self.status]})
        self.status = to_status
