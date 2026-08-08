from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class CompanyMembershipDTO:
    id: UUID
    status: str
    company_id: UUID
    user_id: UUID
    membership_role: str
    is_primary_contact: bool
    invited_at: datetime | None
    joined_at: datetime | None
    left_at: datetime | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None
