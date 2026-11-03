from abc import ABC, abstractmethod
from typing import Any


class BaseIntegrationAdapter(ABC):
    @abstractmethod
    async def test_connection(self, credentials: dict[str, Any]) -> bool:
        """Overí skutočné spojenie s externým systémom."""
        raise NotImplementedError

    @abstractmethod
    async def sync_data(
        self,
        credentials: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Vykoná skutočnú synchronizáciu."""
        raise NotImplementedError
