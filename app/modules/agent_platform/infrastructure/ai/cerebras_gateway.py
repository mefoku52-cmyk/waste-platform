"""Cerebras API gateway — OpenAI-kompatibilný chat completions.

Cerebras beží ako 1. fallback po Groq (chain: groq → cerebras → mistral).
OpenAI-kompatibilné rozhranie: POST /v1/chat/completions s
{"model", "messages", "temperature"[, "tools"]}.

Env:
- CEREBRAS_API_KEY (povinné pre volanie)
- CEREBRAS_API_URL (default https://api.cerebras.ai/v1/chat/completions)
- CEREBRAS_MODEL (default llama-3.3-70b)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from typing import Any

from app.modules.agent_platform.infrastructure.ai._net import (
    log_http_error,
    resolve_url,
)
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

_log = logging.getLogger(__name__)

_UA = "CMEP/1.0 (Cerebras gateway)"
_DEFAULT_URL = "https://api.cerebras.ai/v1/chat/completions"
_DEFAULT_MODEL = "gpt-oss-120b"


class CerebrasModelGateway(ModelGateway):
    def provider_name(self) -> str:
        return "cerebras"

    def _url(self) -> str:
        return resolve_url(os.getenv("CEREBRAS_API_URL"), _DEFAULT_URL, "CEREBRAS_API_URL")

    def _model(self, request: ModelRequest) -> str:
        # CEREBRAS_MODEL je autorita — orchestrátor posiela request.model
        # ("openai/gpt-oss-120b" pre Groq), ktorý Cerebras nehostuje.
        return os.getenv("CEREBRAS_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

    def _build_body(self, request: ModelRequest, *, stream: bool = False) -> dict[str, Any]:
        key = os.getenv("CEREBRAS_API_KEY", "").strip()
        if not key:
            raise RuntimeError("CEREBRAS_API_KEY missing")

        messages: list[dict[str, Any]] = []
        for msg in request.messages:
            payload: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                payload["content"] = msg.content
            if msg.tool_call_id is not None:
                payload["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls is not None:
                payload["tool_calls"] = list(msg.tool_calls)
            messages.append(payload)

        body: dict[str, Any] = {
            "model": self._model(request),
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.tools:
            body["tools"] = list(request.tools)
            body["tool_choice"] = request.tool_choice or "auto"
        if stream:
            body["stream"] = True
        return body

    def _headers(self) -> dict[str, str]:
        key = os.getenv("CEREBRAS_API_KEY", "").strip()
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": _UA,
            "Accept": "application/json",
        }

    async def generate(self, request: ModelRequest) -> ModelResponse:
        body = self._build_body(request)
        data = json.dumps(body).encode("utf-8")
        http = urllib.request.Request(
            self._url(),
            data=data,
            method="POST",
            headers=self._headers(),
        )

        def _do_request():
            with urllib.request.urlopen(http, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))

        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                payload = await asyncio.to_thread(_do_request)
                break
            except urllib.error.HTTPError as e:
                last_exc = e
                if e.code == 429 and attempt < 1:
                    await asyncio.sleep(1)
                    continue
                log_http_error(_log, "cerebras", e)
                raise
        else:
            if last_exc:
                raise last_exc
            raise RuntimeError("cerebras request failed")

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("cerebras empty choices")

        choice = choices[0]
        message = choice.get("message", {}) or {}
        content = message.get("content") or ""
        tool_calls_raw = message.get("tool_calls") or []

        tool_calls: list[dict[str, Any]] = []
        for tc in tool_calls_raw:
            fn = tc.get("function", {}) or {}
            tool_calls.append(
                {
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": fn.get("name", ""),
                        "arguments": fn.get("arguments", "{}"),
                    },
                }
            )

        return ModelResponse(
            request_id=request.request_id,
            text=str(content),
            finish_reason=str(choice.get("finish_reason", "stop")),
            tool_calls=tuple(tool_calls),
            provider_metadata={"provider": "cerebras", "model": payload.get("model", "")},
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Cerebras SSE streaming — nie je primárne využívaný, fallback na generate()."""
        response = await self.generate(request)
        if response.text:
            yield response.text
