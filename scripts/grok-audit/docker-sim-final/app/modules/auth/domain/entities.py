from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class RefreshSession:
    user_id: UUID
    token_family_id: str
    refresh_token_jti: str
    refresh_token_hash: str
    expires_at: datetime

    revoked_at: datetime | None = None
    replaced_by_jti: str | None = None
    reuse_detected_at: datetime | None = None

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by_user_id: UUID | None = None
    updated_by_user_id: UUID | None = None
