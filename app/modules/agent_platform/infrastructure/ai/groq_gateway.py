from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class GroqModelGateway(ModelGateway):
    def provider_name(self) -> str:
        return "groq"

    async def generate(self, request: ModelRequest) -> ModelResponse:
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

        data = json.dumps(body).encode("utf-8")
        http = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": _UA,
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(http, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

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
