"""Chain model gateway — skúša gatewaye v poradí, prvý úspech vyhráva.

Produkčné poradie je **Cerebras → Groq → Mistral** (``PROVIDER_ORDER``).
Keď primárny provider zlyhá (429, timeout, 5xx, chýbajúci kľúč, neplatná
odpoveď), skúsi sa ďalší. Ak zlyhajú všetky, vyhodí sa posledná chyba.

Časové limity:
* ``AI_PROVIDER_TIMEOUT_SECONDS`` (default 20 s) — max. čakanie na jeden
  provider, aby pomalý primárny provider nezablokoval fallback.
* ``AI_CHAIN_TIMEOUT_SECONDS`` (default 45 s) — max. trvanie celého reťazca,
  aby odpoveď stihla prísť skôr než frontendový 60 s timeout.

Fallback sa týka iba generovania odpovede — žiadny nástroj sa v gatewayi
nevykonáva, takže opakovanie požiadavky nemôže spustiť tool dvakrát.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator

from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

logger = logging.getLogger(__name__)

# Jediné miesto, kde je definované poradie providerov pre chat agenta.
PROVIDER_ORDER: tuple[str, ...] = ("cerebras",)

_DEFAULT_PROVIDER_TIMEOUT_S = 20.0
_DEFAULT_TOTAL_TIMEOUT_S = 45.0


def _positive_float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("invalid %s=%r — using default %.1fs", name, raw, default)
        return default
    return value if value > 0 else default


def build_default_model_chain() -> ChainModelGateway:
    """Build the production chain in the documented order.

    Imported lazily so the gateway modules stay independent and tests can
    monkeypatch individual providers.
    """
    from app.modules.agent_platform.infrastructure.ai.cerebras_gateway import (
        CerebrasModelGateway,
    )

    return ChainModelGateway([CerebrasModelGateway()])


class ChainModelGateway(ModelGateway):
    """Skúsi gatewaye postupne; prvý úspech sa vráti, inak raise poslednej chyby."""

    def __init__(
        self,
        gateways: list[ModelGateway],
        *,
        provider_timeout_s: float | None = None,
        total_timeout_s: float | None = None,
    ) -> None:
        if not gateways:
            raise ValueError("ChainModelGateway requires at least one gateway")
        self._gateways = list(gateways)
        self._provider_timeout_s = (
            provider_timeout_s
            if provider_timeout_s is not None and provider_timeout_s > 0
            else _positive_float_env("AI_PROVIDER_TIMEOUT_SECONDS", _DEFAULT_PROVIDER_TIMEOUT_S)
        )
        self._total_timeout_s = (
            total_timeout_s
            if total_timeout_s is not None and total_timeout_s > 0
            else _positive_float_env("AI_CHAIN_TIMEOUT_SECONDS", _DEFAULT_TOTAL_TIMEOUT_S)
        )

    def provider_name(self) -> str:
        return self._gateways[0].provider_name()

    def provider_names(self) -> tuple[str, ...]:
        return tuple(gw.provider_name() for gw in self._gateways)

    async def _generate_with_timeout(
        self,
        gateway: ModelGateway,
        request: ModelRequest,
        *,
        deadline: float,
    ) -> ModelResponse:
        loop = asyncio.get_running_loop()
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise TimeoutError("chain deadline exceeded")
        timeout = min(self._provider_timeout_s, remaining)
        return await asyncio.wait_for(gateway.generate(request), timeout=timeout)

    async def generate(self, request: ModelRequest) -> ModelResponse:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._total_timeout_s
        last_exc: Exception | None = None
        for gw in self._gateways:
            try:
                return await self._generate_with_timeout(gw, request, deadline=deadline)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "chain_gateway_failed provider=%s type=%s — trying next",
                    gw.provider_name(),
                    type(exc).__name__,
                )
                continue
        # Vsetky zlyhali — vyhod poslednu chybu (nie prvu).
        raise last_exc or RuntimeError("all chain gateways failed")

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Stream — skúša gatewaye v poradí.

        Ak provider začal posielať text a až potom zlyhal, do ďalšieho
        providera sa NEPREPÍNA. Inak by používateľ videl duplicitný alebo
        zmiešaný text z dvoch modelov. Chyba sa v tom prípade propaguje.
        """
        for gw in self._gateways:
            yielded = False
            try:
                async for chunk in gw.stream(request):  # ty: ignore[unresolved-attribute]
                    yielded = True
                    yield chunk
                return
            except Exception as exc:
                logger.warning(
                    "chain_stream_failed provider=%s type=%s yielded=%s",
                    gw.provider_name(),
                    type(exc).__name__,
                    yielded,
                )
                if yielded:
                    raise
                continue
        raise RuntimeError("all chain gateways failed")
