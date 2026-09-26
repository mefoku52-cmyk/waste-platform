from __future__ import annotations

from abc import ABC, abstractmethod

from .model_request import ModelRequest
from .model_response import ModelResponse


class ModelGateway(ABC):
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError
