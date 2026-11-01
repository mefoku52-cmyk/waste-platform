"""Adapter nad modelom - abstrakcia, iba citanie, deterministicke chovanie.

ModelAdapter je abstraktny bazovy trieda pre interakciu s modelom.
Predvoleny rezim je ExecutionMode.DISABLED - ziadne volania modelu sa
nevykonaju kym nie je explicitne povolene. MockAdapter je deterministicka
implementacia bez potreby API kluča.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .execution_policy import ExecutionMode, ExecutionPolicy


@dataclass(frozen=True)
class ModelRequest:
    """Vstupny poziadavka pre model."""

    prompt: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    """Vystup z modelu. Nemenne (frozen) pre bezpecnost a predvidatelnost."""

    adapter: str
    result: str
    deterministic: bool
    mode: str
    available: bool
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelAdapter(abc.ABC):
    """Abstrakcia nad modelom. Predvoleny rezim DISABLED - ziadne volania modelu."""

    def __init__(self, policy: ExecutionPolicy | None = None):
        self.policy = policy or ExecutionPolicy()  # DISABLED je predvoleny

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Nazov adaptera."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Ci je adapter disponibilny (napr. API kluc nastaveny)."""
        raise NotImplementedError

    @abc.abstractmethod
    def _infer_impl(self, prompt: str, context: dict[str, Any] | None) -> ModelResponse:
        """Skutocna implementacia inferencie (podtrieda musi definovat)."""
        raise NotImplementedError

    def _is_deterministic(self) -> bool:
        """Ci adapter produkuje deterministicke vysledky."""
        return False

    def infer(self, prompt: str, context: dict[str, Any] | None = None) -> ModelResponse:
        """Vykonaj inferenciu s kontrolou bezpecnostneho rezimu.

        V rezime DISABLED sa model nevola - vracia sa disabled odpoved.
        """
        if self.policy.mode == ExecutionMode.DISABLED:
            return ModelResponse(
                adapter=self.name,
                result="",
                deterministic=self._is_deterministic(),
                mode=self.policy.mode.value,
                available=False,
                error="Vykonanie je vypnute (DISABLED)",
            )
        if not self.policy.is_allowed("diagnose"):
            return ModelResponse(
                adapter=self.name,
                result="",
                deterministic=self._is_deterministic(),
                mode=self.policy.mode.value,
                available=False,
                error="Operacia 'diagnose' nie je povolena politikou",
            )
        return self._infer_impl(prompt, context)

    def analyze(self, prompt: str, context: dict[str, Any] | None = None) -> ModelResponse:
        """Analyzuje vstup prostrednictvom modelu (alias pre infer)."""
        return self.infer(prompt, context)
