"""Testy MistralModelGateway — mock urllib, bez realneho Mistral volania.

Kľúčový regresný bod: request.model ("openai/gpt-oss-120b" z orchestrátora)
sa NESMIE posielať do Mistral — MISTRAL_MODEL je autorita
(bezplatný tier "mistral-small-latest").
"""

import json
import urllib.request

import pytest

from app.modules.agent_platform.infrastructure.ai.mistral_gateway import (
    MistralModelGateway,
)
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)

_MODEL = "mistral-small-latest"


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False


def make_request(**overrides) -> ModelRequest:
    kwargs = {
        "request_id": "req-1",
        "model": "openai/gpt-oss-120b",  # orchestrator sa takto pýta
        "messages": (ModelMessage(role="user", content="Ahoj"),),
    }
    kwargs.update(overrides)
    return ModelRequest(**kwargs)


def _patch_urlopen(monkeypatch, response=None, error=None):
    calls: list = []

    def fake_urlopen(http, *args, **kwargs):
        calls.append(http)
        if error is not None:
            raise error
        return response

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


def _ok_payload() -> bytes:
    payload = {
        "model": _MODEL,
        "choices": [
            {"message": {"role": "assistant", "content": "Dobry den"}, "finish_reason": "stop"}
        ],
    }
    return json.dumps(payload).encode("utf-8")


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")


# --- Provider ----------------------------------------------------------


def test_provider_name():
    assert MistralModelGateway().provider_name() == "mistral"


# --- Model routing (regresia) ------------------------------------------


@pytest.mark.asyncio
async def test_model_comes_from_env_not_request_model(monkeypatch):
    # MISTRAL_MODEL v env vyhráva — request.model "openai/gpt-oss-120b" sa ignoruje.
    monkeypatch.setenv("MISTRAL_MODEL", _MODEL)
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await MistralModelGateway().generate(make_request())

    sent = json.loads(calls[0].data.decode("utf-8"))
    assert sent["model"] == _MODEL


@pytest.mark.asyncio
async def test_missing_env_uses_default_small_model(monkeypatch):
    monkeypatch.delenv("MISTRAL_MODEL", raising=False)
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await MistralModelGateway().generate(make_request(model="openai/gpt-oss-120b"))

    sent = json.loads(calls[0].data.decode("utf-8"))
    # Default "mistral-small-latest" (bezplatný tier), NIE request.model.
    assert sent["model"] == "mistral-small-latest"


# --- Happy path --------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_completion_returns_parsed_response(monkeypatch):
    monkeypatch.setenv("MISTRAL_MODEL", _MODEL)
    _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    result = await MistralModelGateway().generate(make_request())

    assert result.text == "Dobry den"
    assert result.finish_reason == "stop"
    assert result.provider_metadata["provider"] == "mistral"


@pytest.mark.asyncio
async def test_request_body_and_headers(monkeypatch):
    monkeypatch.setenv("MISTRAL_MODEL", _MODEL)
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await MistralModelGateway().generate(make_request(temperature=0.7))

    [http] = calls
    sent = json.loads(http.data.decode("utf-8"))
    assert sent["model"] == _MODEL
    assert sent["temperature"] == 0.7
    assert sent["messages"] == [{"role": "user", "content": "Ahoj"}]
    assert http.headers["Authorization"] == "Bearer test-key"
    assert http.full_url == "https://api.mistral.ai/v1/chat/completions"


@pytest.mark.asyncio
async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY missing"):
        await MistralModelGateway().generate(make_request())
