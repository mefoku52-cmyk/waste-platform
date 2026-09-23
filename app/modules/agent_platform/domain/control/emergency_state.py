"""Emergency state."""

from dataclasses import dataclass
from datetime import UTC, datetime

from .control_mode import ControlMode


@dataclass(frozen=True, slots=True)
class EmergencyState:
    """Current emergency/control state."""

    mode: ControlMode
    changed_at: datetime
    changed_by: str
    reason: str

    def __post_init__(self) -> None:
        if self.changed_at.tzinfo is None:
            raise ValueError("changed_at must be timezone-aware")
        if not self.changed_by.strip():
            raise ValueError("changed_by is required")
        if not self.reason.strip():
            raise ValueError("reason is required")

    @classmethod
    def normal(cls, changed_by: str = "system") -> "EmergencyState":
        return cls(
            mode=ControlMode.NORMAL,
            changed_at=datetime.now(UTC),
            changed_by=changed_by,
            reason="normal operation",
        )
