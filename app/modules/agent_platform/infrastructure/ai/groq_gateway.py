from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from typing import Any

from app.modules.agent_platform.infrastructure.ai._net import log_http_error
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

_log = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class GroqModelGateway(ModelGateway):
    def provider_name(self) -> str:
        return "groq"

    def _build_body(self, request: ModelRequest, *, stream: bool = False) -> dict[str, Any]:
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GROQ_API_KEY missing")

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
            "model": request.model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
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
        key = os.getenv("GROQ_API_KEY", "").strip()
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
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            method="POST",
            headers=self._headers(),
        )

        def _do_request():
            with urllib.request.urlopen(http, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))

        # Retry pri 429 s backoff

        last_exc = None
        for attempt in range(3):
            try:
                payload = await asyncio.to_thread(_do_request)
                break
            except urllib.error.HTTPError as e:
                last_exc = e
                if e.code == 429 and attempt < 2:
                    wait = 2**attempt  # 1, 2 sekundy
                    await asyncio.sleep(wait)
                    continue
                log_http_error(_log, "groq", e)
                raise
        else:
            if last_exc:
                raise last_exc
            raise RuntimeError("groq request failed")

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("groq empty choices")

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
            provider_metadata={"provider": "groq", "model": payload.get("model", "")},
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[str]:
        """Yield text deltas z Groq SSE streamu (A1.2/A1.3).

        Blokujuce citanie urllib ide cez asyncio.to_thread,
        aby sme nezablokovali event loop.
        """
        body = self._build_body(request, stream=True)
        headers = self._headers()
        headers["Accept"] = "text/event-stream"
        data = json.dumps(body).encode("utf-8")
        http = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            method="POST",
            headers=headers,
        )

        resp = await asyncio.to_thread(urllib.request.urlopen, http, timeout=60)
        try:
            while True:
                raw = await asyncio.to_thread(resp.readline)
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                for choice in chunk.get("choices") or []:
                    delta = (choice.get("delta") or {}).get("content")
                    if delta:
                        yield str(delta)
        finally:
            resp.close()
