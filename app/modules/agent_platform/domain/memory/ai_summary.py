"""Rolling conversation summary domain entity.

A summary is derived context about older turns of one conversation. It is
treated as UNTRUSTED DATA by the prompt builder — it never carries instructions
and never influences authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AiSummary:
    content: str
    covers: int
    language: str | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.covers < 0:
            raise ValueError("covers must be non-negative")
