"""Fallback adapter - skusa modely podla priority, kym jeden neuspeje.

Dedi z ModelAdapter, takze respektuje ExecutionPolicy (DISABLED default)
a vsetky bezpecnostne kontroly. Mená modelov nie su natvrdo v kode,
ale beru sa z model_config.py.
"""

from __future__ import annotations

from typing import Any

from .execution_policy import ExecutionPolicy
from .model_adapter import ModelAdapter, ModelResponse
from .model_config import MODEL_PRIORITY


class FallbackAdapter(ModelAdapter):
    """Adapter, ktory skusa modely v poradi priority.

    Ak jeden model zlyha (vrati error alebo available=False), skusi dalsi.
    Ak zlyhaju vsetky, vrati ModelResponse s chybou.
    """

    def __init__(
        self,
        adapters: dict[str, ModelAdapter],
        policy: ExecutionPolicy | None = None,
    ):
        super().__init__(policy)
        self._adapters = adapters
        self._priority = MODEL_PRIORITY

    @property
    def name(self) -> str:
        return "fallback"

    def is_available(self) -> bool:
        """Dostupny je, ak je dostupny aspon jeden adapter."""
        return any(adapter.is_available() for adapter in self._adapters.values())

    def _is_deterministic(self) -> bool:
        """Fallback nie je deterministicky (závisí od modelov)."""
        return False

    def _infer_impl(self, prompt: str, context: dict[str, Any] | None) -> ModelResponse:
        """Skusa modely v poradi priority, kym jeden neuspeje."""
        errors: list[str] = []

        for model_name in self._priority:
            adapter = self._adapters.get(model_name)
            if adapter is None:
                errors.append(f"{model_name}: adapter nie je zaregistrovany")
                continue

            if not adapter.is_available():
                errors.append(f"{model_name}: nie je dostupny (chyba API kluc?)")
                continue

            # Zavolame infer() na adapteri (ten si spravi svoje kontroly)
            response = adapter.infer(prompt, context)

            # Ak uspel, vratime odpoved
            if response.available and not response.error:
                return ModelResponse(
                    adapter=self.name,
                    result=response.result,
                    deterministic=False,
                    mode=response.mode,
                    available=True,
                    metadata={
                        **response.metadata,
                        "used_model": model_name,
                        "fallback_chain": self._priority,
                    },
                )

            # Ak zlyhal, zapiseme chybu a skusame dalej
            errors.append(f"{model_name}: {response.error or 'nezname zlyhanie'}")

        # Vsetky modely zlyhali
        return ModelResponse(
            adapter=self.name,
            result="",
            deterministic=False,
            mode=self.policy.mode.value,
            available=False,
            error=f"Vsetky modely zlyhali: {'; '.join(errors)}",
            metadata={"fallback_chain": self._priority, "errors": errors},
        )
