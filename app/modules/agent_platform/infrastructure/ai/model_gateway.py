"""AI model gateway contract."""

from abc import ABC, abstractmethod

from .model_request import ModelRequest
from .model_response import ModelResponse


class ModelGateway(ABC):
    """Provider-neutral model boundary.

    Concrete providers must live behind this interface.

    The gateway MUST NOT receive:
      - database credentials
      - raw SQL
      - shell commands
      - unrestricted filesystem access
      - platform-admin credentials

    A returned tool call is only a model proposal.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError
