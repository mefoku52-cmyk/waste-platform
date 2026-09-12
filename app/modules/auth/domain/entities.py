from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass
class RefreshSession:
    id: UUID
    user_id: UUID
    family_id: str
    jti: str
    expires_at: datetime
    revoked_at: datetime | None = None
    reuse_detected_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
