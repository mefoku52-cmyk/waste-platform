"""Permission resolver contract."""

from abc import ABC, abstractmethod

from ...domain.permission.permission_decision import PermissionDecision
from ...domain.permission.permission_request import PermissionRequest


class PermissionResolver(ABC):
    @abstractmethod
    async def resolve(self, request: PermissionRequest) -> PermissionDecision:
        raise NotImplementedError
