from dataclasses import dataclass
from datetime import datetime

from app.modules.users.domain.enums import UserStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True)
class User(AuditFields):
    status: UserStatus
    email: str
    password_hash: str
    first_name: str
    last_name: str
    display_name: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    last_login_at: datetime | None

    def validate(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValidationDomainError("User email must be valid")
        if not self.first_name:
            raise ValidationDomainError("User first_name is required")
        if not self.last_name:
            raise ValidationDomainError("User last_name is required")

    def transition_status(self, to_status: UserStatus) -> None:
        allowed = {
            UserStatus.INVITED: {UserStatus.ACTIVE, UserStatus.DEACTIVATED},
            UserStatus.ACTIVE: {UserStatus.SUSPENDED, UserStatus.DEACTIVATED},
            UserStatus.SUSPENDED: {UserStatus.ACTIVE, UserStatus.DEACTIVATED},
            UserStatus.DEACTIVATED: set(),
        }
        ensure_transition(
            self.status.value, to_status.value, {s.value for s in allowed[self.status]}
        )
        self.status = to_status
