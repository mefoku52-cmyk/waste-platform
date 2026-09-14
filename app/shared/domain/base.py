from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True, kw_only=True)
class AuditFields:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None


class BaseEntity:
    def touch(self):
        self.updated_at = datetime.now(UTC)
