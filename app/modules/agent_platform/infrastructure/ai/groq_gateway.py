from __future__ import annotations

import json
import os
import urllib.request

from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse


class GroqModelGateway(ModelGateway):
    def provider_name(self) -> str:
        return "groq"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        prompt = ""
        for name in ("prompt", "content", "message", "input", "text"):
            value = getattr(request, name, None)
            if isinstance(value, str) and value.strip():
                prompt = value.strip()
                break
        if not prompt:
            prompt = str(request)
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GROQ_API_KEY missing")
        body = json.dumps(
            {
                "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        http = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(http, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        choices = payload.get("choices") or []
        content = ""
        if choices:
            content = str(choices[0].get("message", {}).get("content") or "")
        if not content:
            raise RuntimeError("groq empty content")
        fields = getattr(ModelResponse, "__dataclass_fields__", {}) or getattr(
            ModelResponse, "__annotations__", {}
        )
        kwargs: dict[str, object] = {}
        for name in fields:
            if name in {"text", "content", "message", "output", "reply"}:
                kwargs[name] = content
            elif name in {"provider", "provider_name"}:
                kwargs[name] = "groq"
        return ModelResponse(**kwargs)
