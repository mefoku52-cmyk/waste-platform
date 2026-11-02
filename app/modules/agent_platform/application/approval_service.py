"""Complete AI write-tool approval workflow with state machine and payload binding."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class RiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"


class ApprovalRequest(BaseModel):
    id: UUID
    actor_id: UUID
    company_id: UUID
    tool_name: str
    arguments: dict[str, Any]
    arguments_hash: str
    description: str
    risk_level: RiskLevel
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: datetime
    created_at: datetime
    resolved_at: datetime | None = None
    resolver_id: UUID | None = None
    executed_at: datetime | None = None
    execution_error: str | None = None


class ApprovalService:
    def __init__(self) -> None:
        self._store: dict[UUID, ApprovalRequest] = {}

    def _hash_args(self, arguments: dict[str, Any]) -> str:
        raw = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def create(
        self,
        actor_id: UUID,
        company_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
        description: str,
        risk_level: RiskLevel = RiskLevel.MEDIUM_RISK,
        ttl_minutes: int = 15,
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            id=uuid4(),
            actor_id=actor_id,
            company_id=company_id,
            tool_name=tool_name,
            arguments=arguments,
            arguments_hash=self._hash_args(arguments),
            description=description,
            risk_level=risk_level,
            expires_at=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
            created_at=datetime.now(UTC),
        )
        self._store[req.id] = req
        return req

    def get(self, request_id: UUID, company_id: UUID) -> ApprovalRequest | None:
        req = self._store.get(request_id)
        if not req or req.company_id != company_id:
            return None
        self._expire_if_needed(req)
        return req

    def _expire_if_needed(self, req: ApprovalRequest) -> None:
        if req.status == ApprovalStatus.PENDING and datetime.now(UTC) > req.expires_at:
            req.status = ApprovalStatus.EXPIRED

    def approve(self, request_id: UUID, company_id: UUID, resolver_id: UUID) -> ApprovalRequest | None:
        req = self.get(request_id, company_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return None
        # In full impl: re-check that resolver has permission to perform the action
        req.status = ApprovalStatus.APPROVED
        req.resolver_id = resolver_id
        req.resolved_at = datetime.now(UTC)
        return req

    def reject(self, request_id: UUID, company_id: UUID, resolver_id: UUID) -> ApprovalRequest | None:
        req = self.get(request_id, company_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return None
        req.status = ApprovalStatus.REJECTED
        req.resolver_id = resolver_id
        req.resolved_at = datetime.now(UTC)
        return req

    def cancel(self, request_id: UUID, company_id: UUID, actor_id: UUID) -> ApprovalRequest | None:
        req = self.get(request_id, company_id)
        if not req or req.status not in (ApprovalStatus.PENDING, ApprovalStatus.APPROVED):
            return None
        if req.actor_id != actor_id:
            return None
        req.status = ApprovalStatus.CANCELLED
        return req

    def mark_executing(self, request_id: UUID, company_id: UUID, expected_hash: str) -> ApprovalRequest | None:
        req = self.get(request_id, company_id)
        if not req or req.status != ApprovalStatus.APPROVED:
            return None
        if req.arguments_hash != expected_hash:
            return None  # payload changed
        req.status = ApprovalStatus.EXECUTING
        return req

    def mark_executed(self, request_id: UUID, company_id: UUID, success: bool, error: str | None = None) -> ApprovalRequest | None:
        req = self.get(request_id, company_id)
        if not req or req.status != ApprovalStatus.EXECUTING:
            return None
        req.status = ApprovalStatus.EXECUTED if success else ApprovalStatus.FAILED
        req.executed_at = datetime.now(UTC)
        req.execution_error = error
        return req


# Global instance for wiring
approval_service = ApprovalService()