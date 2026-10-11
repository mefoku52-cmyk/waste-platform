"""Chain model gateway — skúša gatewaye v poradí, prvý úspech vyhráva.

Ordering: [groq, cerebras, mistral]. Keď primárny zlyhá (429, timeout,
5xx, chýbajúci kľúč), skúsi sa ďalší. Ak zlyhajú všetky, vyhodí sa
posledná chyba (aby bola v logoch), ako to robil FallbackModelGateway.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

logger = logging.getLogger(__name__)


class ChainModelGateway(ModelGateway):
    """Skúsi gatewaye postupne; prvý úspech sa vráti, inak raise poslednej chyby."""

    def __init__(self, gateways: list[ModelGateway]) -> None:
        if not gateways:
            raise ValueError("ChainModelGateway requires at least one gateway")
        self._gateways = list(gateways)

    def provider_name(self) -> str:
        return self._gateways[0].provider_name()

    async def generate(self, request: ModelRequest) -> ModelResponse:
        last_exc: Exception | None = None
        for gw in self._gateways:
            try:
                return await gw.generate(request)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "chain_gateway_failed provider=%s type=%s — trying next",
                    gw.provider_name(),
                    type(exc).__name__,
                )
                continue
        # Vsetky zlyhali — vyhod poslednu chybu (nie prvu), ako FallbackModelGateway.
        raise last_exc or RuntimeError("all chain gateways failed")

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Stream — skúša gatewaye v poradí.

        Poznámka: ak chyba príde až po prvom yielde, už sa nedá prepnúť —
        použije sa to, čo prišlo (rovnaké obmedzenie ako FallbackModelGateway).
        """
        for gw in self._gateways:
            try:
                async for chunk in gw.stream(request):  # ty: ignore[unresolved-attribute]
                    yield chunk
                return
            except Exception as exc:
                logger.warning(
                    "chain_stream_failed provider=%s type=%s — trying next",
                    gw.provider_name(),
                    type(exc).__name__,
                )
                continue
