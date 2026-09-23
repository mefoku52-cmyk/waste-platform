"""Approval persistence contract."""

from abc import ABC, abstractmethod

from ...domain.approval.approval_request import ApprovalRequest
from ...domain.approval.approval_status import ApprovalStatus


class ApprovalRepository(ABC):
    @abstractmethod
    async def create(self, approval: ApprovalRequest) -> ApprovalRequest:
        raise NotImplementedError

    @abstractmethod
    async def get(self, approval_id: str) -> ApprovalRequest | None:
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
    ) -> ApprovalRequest:
        raise NotImplementedError
