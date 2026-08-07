from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True, kw_only=True)
class CompanyMembership(AuditFields):
    status: CompanyMembershipStatus
    company_id: UUID
    user_id: UUID
    membership_role: CompanyMembershipRole
    is_primary_contact: bool
    invited_at: datetime | None = None
    joined_at: datetime | None = None
    left_at: datetime | None = None

    def validate(self) -> None:
        if not self.company_id:
            raise ValidationDomainError("Membership company_id is required")
        if not self.user_id:
            raise ValidationDomainError("Membership user_id is required")

    def transition_status(self, to_status: CompanyMembershipStatus) -> None:
        allowed = {
            CompanyMembershipStatus.INVITED: {CompanyMembershipStatus.ACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.ACTIVE: {CompanyMembershipStatus.INACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.INACTIVE: {CompanyMembershipStatus.ACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.REMOVED: set(),
        }
        ensure_transition(self.status.value, to_status.value, {s.value for s in allowed[self.status]})
        self.status = to_status
