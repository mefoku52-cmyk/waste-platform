"""Univerzalny adapter pre lubovolny OpenAI-kompatibilny model.

Nepouziva natvrdo definovane mena modelov. Vsetko sa berie z konfiguracie:
- API URL
- API kluc (z prostredia)
- Nazov modelu

Podporuje: Groq, Mistral, Cerebras, OpenAI, a dalsie, ktore maju
OpenAI-kompatibilne API.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .execution_policy import ExecutionPolicy
from .model_adapter import ModelAdapter, ModelResponse


class GenericAPIAdapter(ModelAdapter):
    """Univerzalny adapter pre OpenAI-kompatibilne API."""

    def __init__(
        self,
        name: str,
        api_url: str,
        api_key_env: str,
        model_name: str,
        policy: ExecutionPolicy | None = None,
    ):
        super().__init__(policy)
        self._name = name
        self._api_url = api_url
        self._api_key_env = api_key_env
        self._model_name = model_name

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return bool(os.environ.get(self._api_key_env, ""))

    def _is_deterministic(self) -> bool:
        return False

    def _infer_impl(self, prompt: str, context: dict[str, Any] | None) -> ModelResponse:
        api_key = os.environ.get(self._api_key_env, "")
        if not api_key:
            return ModelResponse(
                adapter=self._name,
                result="",
                deterministic=False,
                mode=self.policy.mode.value,
                available=False,
                error=f"API kluc '{self._api_key_env}' nie je nastaveny",
            )

        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": "Si navigator pre CMEP. Odpovedaj strucne."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            self._api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data["choices"][0]["message"]["content"]
                return ModelResponse(
                    adapter=self._name,
                    result=result,
                    deterministic=False,
                    mode=self.policy.mode.value,
                    available=True,
                    metadata={"model": self._model_name, "provider": self._name},
                )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return ModelResponse(
                adapter=self._name,
                result="",
                deterministic=False,
                mode=self.policy.mode.value,
                available=False,
                error=f"HTTP {e.code}: {body[:200]}",
            )
        except Exception as exc:
            return ModelResponse(
                adapter=self._name,
                result="",
                deterministic=False,
                mode=self.policy.mode.value,
                available=False,
                error=f"{type(exc).__name__}: {str(exc)[:200]}",
            )
