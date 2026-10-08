"""Fallback model gateway — skúsi primárny (Groq), potom fallback (Mistral).

Rate limit 429 na Groq už neznamená koniec — Mistral prevezme.
Provider info sa vracia v provider_metadata, aby orchestrátor vedel odkiaľ odpoveď prišla.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

logger = logging.getLogger(__name__)


class FallbackModelGateway(ModelGateway):
    """Skúsi primárny gateway, pri chybe fallback gateway."""

    def __init__(
        self,
        *,
        primary: ModelGateway,
        fallback: ModelGateway | None = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    def provider_name(self) -> str:
        return self._primary.provider_name()

    async def generate(self, request: ModelRequest) -> ModelResponse:
        try:
            return await self._primary.generate(request)
        except Exception as primary_exc:
            if self._fallback is None:
                raise
            logger.warning(
                "primary_gateway_failed provider=%s type=%s — trying fallback",
                self._primary.provider_name(),
                type(primary_exc).__name__,
            )
            try:
                return await self._fallback.generate(request)
            except Exception as fallback_exc:
                logger.exception(
                    "fallback_gateway_failed provider=%s type=%s",
                    self._fallback.provider_name(),
                    type(fallback_exc).__name__,
                )
                # Ak zlyhali oba, vyhodí prvú chybu (aby bola v logoch)
                raise primary_exc from fallback_exc

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Stream — skúsi primárny stream, pri chybe hneď fallback stream.

        Poznámka: chyba sa môže objaviť až po prvom yielde. Vtedy už
        nie je možné prepnúť — použije sa to, čo prišlo.
        """
        if self._fallback is None:
            async for chunk in self._primary.stream(request):  # ty: ignore[unresolved-attribute]
                yield chunk
            return

        try:
            async for chunk in self._primary.stream(request):  # ty: ignore[unresolved-attribute]
                yield chunk
            return
        except Exception as primary_exc:
            logger.warning(
                "primary_stream_failed provider=%s type=%s — trying fallback stream",
                self._primary.provider_name(),
                type(primary_exc).__name__,
            )

        async for chunk in self._fallback.stream(request):  # ty: ignore[unresolved-attribute]
            yield chunk
