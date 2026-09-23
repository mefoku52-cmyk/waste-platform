"""Permission request."""

from dataclasses import dataclass

from .permission_scope import PermissionScope


@dataclass(frozen=True, slots=True)
class PermissionRequest:
    request_id: str
    actor_id: str
    actor_type: str
    scope: PermissionScope
    reason: str

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.actor_id.strip():
            raise ValueError("actor_id is required")
        if not self.actor_type.strip():
            raise ValueError("actor_type is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
