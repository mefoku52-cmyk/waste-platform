"""ChainAdapter nad modelmi - deterministicky skúša viaceré adaptéry postupne.

Použije prvý dostupný adapter; pri chybe poskytovateľa pokračuje na ďalší.
Nevyžaduje API kľúče ani sieťové volania. Rešpektuje ExecutionPolicy a
ExecutionMode.DISABLED (v tomto režime sa žiadny vnútorný adaptér nezavolá).
"""

from __future__ import annotations

from typing import Any

from .execution_policy import ExecutionPolicy
from .model_adapter import ModelAdapter, ModelResponse


class ChainAdapter(ModelAdapter):
    """Zreťazí viaceré adaptery. Skúsi ich postupne; pri chybe prejde na ďalší.

    Nikdy neaplikuje žiadnu mutujúcu operáciu a nikdy nevystaví citlivé
    detaily chýb v vystupnom modeli.
    """

    def __init__(
        self,
        adapters: list[ModelAdapter],
        policy: ExecutionPolicy | None = None,
    ):
        super().__init__(policy)
        self._adapters = list(adapters)

    @property
    def name(self) -> str:
        return "chain:" + ",".join(adapter.name for adapter in self._adapters)

    def is_available(self) -> bool:
        """Vráť True, ak aspoň jeden vnútorný adapter je dostupný."""
        return any(adapter.is_available() for adapter in self._adapters)

    def _is_deterministic(self) -> bool:
        return all(adapter._is_deterministic() for adapter in self._adapters)

    def _infer_impl(self, prompt: str, context: dict[str, Any] | None) -> ModelResponse:
        for adapter in self._adapters:
            if not adapter.is_available():
                continue
            try:
                response = adapter.infer(prompt, context)
                if response.available:
                    return response
            except Exception:  # bezpečne zachytíme libovolnú chybu poskytovateľa
                continue
        # Všetky adaptéry zlyhali alebo nie je dostupný žiadny.
        return ModelResponse(
            adapter=self.name,
            result="",
            deterministic=self._is_deterministic(),
            mode=self.policy.mode.value,
            available=False,
            error="Všetky adaptéry zlyhali alebo nie sú dostupné.",
            metadata={"seed": self.__class__.__name__, "count": len(self._adapters)},
        )
