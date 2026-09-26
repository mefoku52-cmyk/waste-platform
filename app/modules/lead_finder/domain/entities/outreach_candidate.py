"""Outreach candidate domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OutreachStatus(StrEnum):
    NEW = "new"
    DRAFTED = "drafted"
    APPROVED = "approved"
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(slots=True)
class OutreachCandidate:
    id: str
    company_name: str
    ico: str | None
    city: str | None
    industry: str | None
    email: str | None
    status: OutreachStatus
    draft_subject: str | None
    draft_body: str | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    sent_at: datetime | None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.company_name.strip():
            raise ValueError("company_name is required")
