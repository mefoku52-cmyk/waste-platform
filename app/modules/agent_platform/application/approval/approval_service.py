"""Approval service contract."""

from abc import ABC, abstractmethod

from ...domain.approval.approval_decision import ApprovalDecision
from ...domain.approval.approval_request import ApprovalRequest


class ApprovalService(ABC):
    @abstractmethod
    async def request(self, approval: ApprovalRequest) -> ApprovalRequest:
        raise NotImplementedError

    @abstractmethod
    async def decide(self, decision: ApprovalDecision) -> ApprovalDecision:
        raise NotImplementedError


class DefaultApprovalService(ApprovalService):
    """Konkretna implementacia ApprovalService."""

    def __init__(self, *, repository) -> None:
        self._repository = repository

    async def request(self, approval: ApprovalRequest) -> ApprovalRequest:
        return await self._repository.create(approval)

    async def decide(self, decision: ApprovalDecision) -> ApprovalDecision:
        await self._repository.update_status(
            decision.approval_id,
            decision.status,
            decided_at=decision.decided_at,
        )
        return decision
