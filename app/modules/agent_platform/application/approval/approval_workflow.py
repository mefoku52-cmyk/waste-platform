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
