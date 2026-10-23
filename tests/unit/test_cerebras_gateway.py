"""Testy CerebrasModelGateway — bez realneho Cerebras volania (mock urllib).

Rovnaky vzor ako tests/unit/test_groq_gateway.py: FakeResponse nahradza
urlopen, chyby (429, timeout, 5xx, malformed JSON) sa propaguju.
"""

import json
import urllib.error
import urllib.request

import pytest

from app.modules.agent_platform.infrastructure.ai.cerebras_gateway import (
    CerebrasModelGateway,
)
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)

_MODEL = "gpt-oss-120b"


class FakeResponse:
    """Minimalna nahrada odpovede z urllib.request.urlopen."""

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
    """Podstrci urlopen. Vracia zoznam zachytenych Request objektov."""
    calls: list = []

    def fake_urlopen(http, *args, **kwargs):
        calls.append(http)
        if error is not None:
            raise error
        return response

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


def _ok_payload(**message_overrides) -> bytes:
    message = {"role": "assistant", "content": "Dobry den"}
    message.update(message_overrides)
    payload = {
        "model": _MODEL,
        "choices": [{"message": message, "finish_reason": "stop"}],
    }
    return json.dumps(payload).encode("utf-8")


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")
    monkeypatch.setenv("CEREBRAS_MODEL", _MODEL)
    monkeypatch.setenv("CEREBRAS_API_URL", "https://api.cerebras.ai/v1/chat/completions")


# --- Provider ----------------------------------------------------------


def test_provider_name():
    assert CerebrasModelGateway().provider_name() == "cerebras"


# --- Happy path --------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_completion_returns_parsed_response(monkeypatch):
    _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    result = await CerebrasModelGateway().generate(make_request())

    assert result.text == "Dobry den"
    assert result.finish_reason == "stop"
    assert result.request_id == "req-1"
    assert result.tool_calls == ()
    assert result.provider_metadata["provider"] == "cerebras"


@pytest.mark.asyncio
async def test_request_body_and_headers(monkeypatch):
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await CerebrasModelGateway().generate(make_request(temperature=0.7))

    [http] = calls
    sent = json.loads(http.data.decode("utf-8"))
    # CEREBRAS_MODEL je autorita — request.model ("openai/gpt-oss-120b")
    # sa NESMIE poslat do Cerebras.
    assert sent["model"] == _MODEL
    assert sent["temperature"] == 0.7
    assert sent["messages"] == [{"role": "user", "content": "Ahoj"}]
    assert "tools" not in sent
    assert http.headers["Authorization"] == "Bearer test-key"
    assert http.full_url == "https://api.cerebras.ai/v1/chat/completions"


@pytest.mark.asyncio
async def test_env_model_missing_uses_default_model(monkeypatch):
    monkeypatch.delenv("CEREBRAS_MODEL", raising=False)
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await CerebrasModelGateway().generate(make_request(model="openai/gpt-oss-120b"))

    sent = json.loads(calls[0].data.decode("utf-8"))
    assert sent["model"] == _MODEL  # default gpt-oss-120b, nie request.model


@pytest.mark.asyncio
async def test_tools_are_included_with_default_tool_choice(monkeypatch):
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    tool = {"type": "function", "function": {"name": "cmep.company.search"}}
    await CerebrasModelGateway().generate(make_request(tools=(tool,)))

    sent = json.loads(calls[0].data.decode("utf-8"))
    assert sent["tools"] == [tool]
    assert sent["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_tool_calls_are_parsed(monkeypatch):
    body = _ok_payload(
        content=None,
        tool_calls=[
            {
                "id": "call_1",
                "function": {"name": "cmep.company.search", "arguments": '{"q":"ekol"}'},
            }
        ],
    )
    _patch_urlopen(monkeypatch, response=FakeResponse(body))
    result = await CerebrasModelGateway().generate(make_request())

    assert result.text == ""
    [tc] = result.tool_calls
    assert tc["id"] == "call_1"
    assert tc["type"] == "function"
    assert tc["function"]["name"] == "cmep.company.search"
    assert tc["function"]["arguments"] == '{"q":"ekol"}'


# --- Failure modes (vsetky sa PROPAGUJU) --------------------------------


@pytest.mark.asyncio
async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CEREBRAS_API_KEY missing"):
        await CerebrasModelGateway().generate(make_request())


@pytest.mark.asyncio
async def test_http_429_propagates_after_one_retry(monkeypatch):
    err = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
    calls = _patch_urlopen(monkeypatch, error=err)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        await CerebrasModelGateway().generate(make_request())
    assert excinfo.value.code == 429
    assert len(calls) == 2  # 1 pokus + 1 retry po backoffe


@pytest.mark.asyncio
async def test_timeout_propagates(monkeypatch):
    _patch_urlopen(monkeypatch, error=TimeoutError("timed out"))
    with pytest.raises(TimeoutError):
        await CerebrasModelGateway().generate(make_request())


@pytest.mark.asyncio
async def test_empty_choices_raises(monkeypatch):
    _patch_urlopen(monkeypatch, response=FakeResponse(b'{"choices": []}'))
    with pytest.raises(RuntimeError, match="cerebras empty choices"):
        await CerebrasModelGateway().generate(make_request())
