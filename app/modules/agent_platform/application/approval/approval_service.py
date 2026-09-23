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
