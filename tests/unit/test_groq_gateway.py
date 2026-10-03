"""Testy GroqModelGateway — bez realneho Groq volania (mock urllib).

Gateway pouziva urllib.request (nie httpx) a NEMÁ try/except okolo
HTTP volania: chyby (429, timeout, 5xx, malformed JSON) sa propaguju
ako vynimky, nie "graceful fail". FakeResponse nahrádza urlopen.
"""

import json
import urllib.error
import urllib.request

import pytest

from app.modules.agent_platform.infrastructure.ai.groq_gateway import (
    GroqModelGateway,
)
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)

_MODEL = "llama-3.1-8b-instant"


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
        "model": _MODEL,
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
    monkeypatch.setenv("GROQ_API_KEY", "test-key")


# --- Provider ----------------------------------------------------------


def test_provider_name():
    assert GroqModelGateway().provider_name() == "groq"


# --- Happy path --------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_completion_returns_parsed_response(monkeypatch):
    _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    result = await GroqModelGateway().generate(make_request())

    assert result.text == "Dobry den"
    assert result.finish_reason == "stop"
    assert result.request_id == "req-1"
    assert result.tool_calls == ()
    assert result.provider_metadata["provider"] == "groq"


@pytest.mark.asyncio
async def test_request_body_and_headers(monkeypatch):
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    await GroqModelGateway().generate(make_request(temperature=0.7))

    [http] = calls
    sent = json.loads(http.data.decode("utf-8"))
    assert sent["model"] == _MODEL
    assert sent["temperature"] == 0.7
    assert sent["messages"] == [{"role": "user", "content": "Ahoj"}]
    assert "tools" not in sent
    assert http.headers["Authorization"] == "Bearer test-key"
    assert http.full_url.endswith("/openai/v1/chat/completions")


@pytest.mark.asyncio
async def test_tools_are_included_with_default_tool_choice(monkeypatch):
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    tool = {"type": "function", "function": {"name": "cmep.company.search"}}
    await GroqModelGateway().generate(make_request(tools=(tool,)))

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
    result = await GroqModelGateway().generate(make_request())

    assert result.text == ""
    [tc] = result.tool_calls
    assert tc["id"] == "call_1"
    assert tc["type"] == "function"
    assert tc["function"]["name"] == "cmep.company.search"
    assert tc["function"]["arguments"] == '{"q":"ekol"}'


@pytest.mark.asyncio
async def test_tool_message_payload_includes_tool_call_id(monkeypatch):
    calls = _patch_urlopen(monkeypatch, response=FakeResponse(_ok_payload()))
    req = make_request(
        messages=(ModelMessage(role="tool", content="obsah", tool_call_id="call_1"),)
    )
    await GroqModelGateway().generate(req)

    sent = json.loads(calls[0].data.decode("utf-8"))
    assert sent["messages"] == [{"role": "tool", "content": "obsah", "tool_call_id": "call_1"}]


# --- Failure modes (vsetky sa PROPAGUJU, gateway nema try/except) ------


@pytest.mark.asyncio
async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY missing"):
        await GroqModelGateway().generate(make_request())


@pytest.mark.asyncio
async def test_malformed_json_raises(monkeypatch):
    _patch_urlopen(monkeypatch, response=FakeResponse(b"not-json{{"))
    with pytest.raises(json.JSONDecodeError):
        await GroqModelGateway().generate(make_request())


@pytest.mark.asyncio
async def test_http_429_propagates(monkeypatch):
    err = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
    _patch_urlopen(monkeypatch, error=err)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        await GroqModelGateway().generate(make_request())
    assert excinfo.value.code == 429


@pytest.mark.asyncio
async def test_timeout_propagates(monkeypatch):
    _patch_urlopen(monkeypatch, error=TimeoutError("timed out"))
    with pytest.raises(TimeoutError):
        await GroqModelGateway().generate(make_request())


@pytest.mark.asyncio
async def test_http_500_propagates(monkeypatch):
    err = urllib.error.HTTPError("u", 500, "Server Error", {}, None)
    _patch_urlopen(monkeypatch, error=err)
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        await GroqModelGateway().generate(make_request())
    assert excinfo.value.code == 500


@pytest.mark.asyncio
async def test_empty_choices_raises(monkeypatch):
    _patch_urlopen(monkeypatch, response=FakeResponse(b'{"choices": []}'))
    with pytest.raises(RuntimeError, match="groq empty choices"):
        await GroqModelGateway().generate(make_request())
