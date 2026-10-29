"""Testy pre FallbackAdapter - overuju prepinanie modelov."""

from __future__ import annotations

import pytest

from app.modules.agent_platform.navigator.model_adapter import ModelAdapter, ModelResponse
from app.modules.agent_platform.navigator.execution_policy import ExecutionPolicy, ExecutionMode
from app.modules.agent_platform.navigator.fallback_adapter import FallbackAdapter
from app.modules.agent_platform.navigator.model_config import MODEL_PRIORITY


class FakeAdapter(ModelAdapter):
    """Fake adapter pre testovanie."""

    def __init__(self, name: str, available: bool = True, should_fail: bool = False):
        super().__init__(policy=ExecutionPolicy(mode=ExecutionMode.DRY_RUN))
        self._name = name
        self._available = available
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def _infer_impl(self, prompt: str, context: dict | None) -> ModelResponse:
        if self._should_fail:
            return ModelResponse(
                adapter=self._name,
                result="",
                deterministic=False,
                mode=self.policy.mode.value,
                available=False,
                error="Simulovane zlyhanie",
            )
        return ModelResponse(
            adapter=self._name,
            result=f"Odpoved od {self._name}",
            deterministic=False,
            mode=self.policy.mode.value,
            available=True,
        )


def test_fallback_pouje_prvy_dostupny_model():
    """Ak je prvy model dostupny, pouzije sa on."""
    adapters = {
        MODEL_PRIORITY[0]: FakeAdapter(MODEL_PRIORITY[0], available=True),
        MODEL_PRIORITY[1]: FakeAdapter(MODEL_PRIORITY[1], available=True),
        MODEL_PRIORITY[2]: FakeAdapter(MODEL_PRIORITY[2], available=True),
    }
    router = FallbackAdapter(adapters, policy=ExecutionPolicy(mode=ExecutionMode.DRY_RUN))
    result = router.infer("test")
    assert result.available is True
    assert result.metadata["used_model"] == MODEL_PRIORITY[0]


def test_fallback_preskoci_nedostupny_model():
    """Ak prvy model nie je dostupny, pouzije sa druhy."""
    adapters = {
        MODEL_PRIORITY[0]: FakeAdapter(MODEL_PRIORITY[0], available=False),
        MODEL_PRIORITY[1]: FakeAdapter(MODEL_PRIORITY[1], available=True),
        MODEL_PRIORITY[2]: FakeAdapter(MODEL_PRIORITY[2], available=True),
    }
    router = FallbackAdapter(adapters, policy=ExecutionPolicy(mode=ExecutionMode.DRY_RUN))
    result = router.infer("test")
    assert result.available is True
    assert result.metadata["used_model"] == MODEL_PRIORITY[1]


def test_fallback_preskoci_zlyhany_model():
    """Ak prvy model zlyha (error), pouzije sa druhy."""
    adapters = {
        MODEL_PRIORITY[0]: FakeAdapter(MODEL_PRIORITY[0], available=True, should_fail=True),
        MODEL_PRIORITY[1]: FakeAdapter(MODEL_PRIORITY[1], available=True),
        MODEL_PRIORITY[2]: FakeAdapter(MODEL_PRIORITY[2], available=True),
    }
    router = FallbackAdapter(adapters, policy=ExecutionPolicy(mode=ExecutionMode.DRY_RUN))
    result = router.infer("test")
    assert result.available is True
    assert result.metadata["used_model"] == MODEL_PRIORITY[1]


def test_fallback_vrati_chybu_ak_vsetky_zlyhaju():
    """Ak vsetky modely zlyhaju, vrati chybu."""
    adapters = {
        MODEL_PRIORITY[0]: FakeAdapter(MODEL_PRIORITY[0], available=True, should_fail=True),
        MODEL_PRIORITY[1]: FakeAdapter(MODEL_PRIORITY[1], available=True, should_fail=True),
        MODEL_PRIORITY[2]: FakeAdapter(MODEL_PRIORITY[2], available=True, should_fail=True),
    }
    router = FallbackAdapter(adapters, policy=ExecutionPolicy(mode=ExecutionMode.DRY_RUN))
    result = router.infer("test")
    assert result.available is False
    assert "Vsetky modely zlyhali" in result.error


def test_fallback_respektuje_disabled():
    """Ak je rezim DISABLED, fallback nic nevola."""
    adapters = {
        MODEL_PRIORITY[0]: FakeAdapter(MODEL_PRIORITY[0], available=True),
        MODEL_PRIORITY[1]: FakeAdapter(MODEL_PRIORITY[1], available=True),
        MODEL_PRIORITY[2]: FakeAdapter(MODEL_PRIORITY[2], available=True),
    }
    router = FallbackAdapter(adapters, policy=ExecutionPolicy(mode=ExecutionMode.DISABLED))
    result = router.infer("test")
    assert result.available is False
    assert "DISABLED" in result.error
