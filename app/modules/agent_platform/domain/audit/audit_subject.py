"""Audit subject."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuditSubject:
    subject_type: str
    subject_id: str

    def __post_init__(self) -> None:
        if not self.subject_type.strip():
            raise ValueError("subject_type is required")
        if not self.subject_id.strip():
            raise ValueError("subject_id is required")
