"""Approval workflow contract."""

from abc import ABC, abstractmethod

from ...domain.approval.approval_request import ApprovalRequest


class ApprovalWorkflow(ABC):
    @abstractmethod
    async def start(self, approval: ApprovalRequest) -> ApprovalRequest:
        raise NotImplementedError

    @abstractmethod
    async def is_executable(self, approval_id: str) -> bool:
        raise NotImplementedError


class DefaultApprovalWorkflow(ApprovalWorkflow):
    """Konkretna implementacia ApprovalWorkflow.

    start() ulozi request. is_executable() overi, ci je schvaleny
    a neexpirovany.
    """

    def __init__(self, *, repository=None) -> None:
        self._repository = repository

    async def start(self, approval: ApprovalRequest) -> ApprovalRequest:
        if self._repository is None:
            return approval
        return await self._repository.create(approval)

    async def is_executable(self, approval_id: str) -> bool:
        from datetime import UTC, datetime

        from app.modules.agent_platform.domain.approval.approval_status import (
            ApprovalStatus,
        )

        if self._repository is None:
            return False
        existing = await self._repository.get(approval_id)
        if existing is None:
            return False
        if existing.status != ApprovalStatus.APPROVED:
            return False
        now = datetime.now(UTC)
        expires_at = existing.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at > now
