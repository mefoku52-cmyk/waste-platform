"""Permission engine contract."""

from abc import ABC, abstractmethod

from ...domain.permission.permission_decision import PermissionDecision
from ...domain.permission.permission_request import PermissionRequest


class PermissionEngine(ABC):
    @abstractmethod
    async def authorize(self, request: PermissionRequest) -> PermissionDecision:
        raise NotImplementedError
