"""Permission scope."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionScope:
    """Explicit scope for a permission."""

    resource: str
    action: str
    owner_id: str | None = None
    company_id: str | None = None

    def __post_init__(self) -> None:
        if not self.resource.strip():
            raise ValueError("resource is required")
        if not self.action.strip():
            raise ValueError("action is required")
