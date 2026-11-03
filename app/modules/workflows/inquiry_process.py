"""Inquiry lifecycle process manager (saga)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class InquiryProcessState(str, Enum):
    CREATED = "created"
    SELLER_NOTIFIED = "seller_notified"
    ANSWERED = "answered"
    CONTACT_REVEALED = "contact_revealed"
    CLOSED = "closed"
    FAILED = "failed"


class InquiryProcess(BaseModel):
    id: UUID
    inquiry_id: UUID
    state: InquiryProcessState
    actor_id: UUID | None = None
    updated_at: datetime
    error: str | None = None


class InquiryProcessManager:
    def __init__(self) -> None:
        self._processes: dict[UUID, InquiryProcess] = {}

    async def start(self, inquiry_id: UUID, actor_id: UUID | None = None) -> InquiryProcess:
        proc = InquiryProcess(
            id=inquiry_id,  # simplified
            inquiry_id=inquiry_id,
            state=InquiryProcessState.CREATED,
            actor_id=actor_id,
            updated_at=datetime.now(UTC),
        )
        self._processes[inquiry_id] = proc
        return proc

    async def transition(self, inquiry_id: UUID, new_state: InquiryProcessState, actor_id: UUID | None = None) -> InquiryProcess | None:
        proc = self._processes.get(inquiry_id)
        if not proc:
            return None
        # Re-check permissions would happen here in full impl
        proc.state = new_state
        proc.actor_id = actor_id
        proc.updated_at = datetime.now(UTC)
        return proc