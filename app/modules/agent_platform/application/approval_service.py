"""AI write-tool approval workflow models."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    id: UUID
    actor_id: UUID
    company_id: UUID
    tool_name: str
    arguments: dict
    description: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: datetime
    created_at: datetime
    resolved_at: datetime | None = None


class ApprovalService:
    def __init__(self) -> None:
        self._store: dict[UUID, ApprovalRequest] = {}

    def create(self, actor_id: UUID, company_id: UUID, tool_name: str, arguments: dict, description: str, ttl_minutes: int = 15) -> ApprovalRequest:
        req = ApprovalRequest(
            id=uuid4(),
            actor_id=actor_id,
            company_id=company_id,
            tool_name=tool_name,
            arguments=arguments,
            description=description,
            expires_at=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
            created_at=datetime.now(UTC),
        )
        self._store[req.id] = req
        return req

    def resolve(self, request_id: UUID, approved: bool, resolver_id: UUID) -> ApprovalRequest | None:
        req = self._store.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return None
        if datetime.now(UTC) > req.expires_at:
            req.status = ApprovalStatus.EXPIRED
            return req
        # In full impl re-check that resolver has permission
        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.resolved_at = datetime.now(UTC)
        return req