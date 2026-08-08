from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class UserDTO:
    id: UUID
    status: str
    email: str
    first_name: str
    last_name: str
    display_name: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    last_login_at: datetime | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None
