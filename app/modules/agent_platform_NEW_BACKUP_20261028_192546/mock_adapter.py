"""Deterministicky mock adapter - nevyžaduje API kluc.

MockAdapter produkujePredvidelne, deterministicke vysledky na zaklade
SHA-256 hash-u vstupu. Pouziva sa pre testovanie a simulaciu bez nutnosti
pripojenia k skutočnemu modelu ani API kluča.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .model_adapter import ModelAdapter, ModelResponse


class MockAdapter(ModelAdapter):
    """Deterministicky mock adapter. Nevyžaduje API kluc ani sieťové pripojenie."""

    def __init__(self, policy=None, seed: str = "mock"):
        super().__init__(policy)
        self._seed = seed

    @property
    def name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        """Mock vzdy je dostupny - nevyžaduje API kluc."""
        return True

    def _is_deterministic(self) -> bool:
        return True

    def _infer_impl(self, prompt: str, context: dict[str, Any] | None) -> ModelResponse:
        """Deterministicky vysledok na zaklade SHA-256(seed + prompt)."""
        digest = hashlib.sha256((self._seed + "|" + prompt).encode("utf-8")).hexdigest()
        result = f"mock:{digest[:16]}"
        metadata: dict[str, Any] = {"seed": self._seed, "hash": digest}
        if context:
            metadata["context_keys"] = sorted(context.keys())
        return ModelResponse(
            adapter=self.name,
            result=result,
            deterministic=True,
            mode=self.policy.mode.value,
            available=True,
            metadata=metadata,
        )
