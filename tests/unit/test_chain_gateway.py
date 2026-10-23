"""Testy ChainModelGateway — fallback ordering (groq → cerebras → mistral)."""

import pytest

from app.modules.agent_platform.infrastructure.ai.chain_gateway import ChainModelGateway
from app.modules.agent_platform.infrastructure.ai.model_gateway import ModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import ModelRequest
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse


class StubGateway(ModelGateway):
    """Gateway stub so zvolenou chybou alebo odpovedou."""

    def __init__(self, name: str, *, error: Exception | None = None, text: str = "ok"):
        self._name = name
        self._error = error
        self._text = text
        self.calls = 0

    def provider_name(self) -> str:
        return self._name

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return ModelResponse(
            request_id=request.request_id,
            text=self._text,
            finish_reason="stop",
            tool_calls=(),
            provider_metadata={"provider": self._name},
        )


def _req() -> ModelRequest:
    return ModelRequest(
        request_id="req-1",
        model="openai/gpt-oss-120b",
        messages=(),
    )


def test_requires_at_least_one_gateway():
    with pytest.raises(ValueError, match="at least one gateway"):
        ChainModelGateway([])


def test_provider_name_is_first_gateway():
    chain = ChainModelGateway([StubGateway("groq"), StubGateway("cerebras")])
    assert chain.provider_name() == "groq"


@pytest.mark.asyncio
async def test_first_gateway_wins_when_ok():
    groq = StubGateway("groq", text="z groq")
    cerebras = StubGateway("cerebras")
    chain = ChainModelGateway([groq, cerebras])

    result = await chain.generate(_req())

    assert groq.calls == 1
    assert cerebras.calls == 0
    assert result.text == "z groq"
    assert result.provider_metadata["provider"] == "groq"


@pytest.mark.asyncio
async def test_second_gateway_used_when_first_fails():
    groq = StubGateway("groq", error=RuntimeError("groq down"))
    cerebras = StubGateway("cerebras", text="z cerebras")
    mistral = StubGateway("mistral")
    chain = ChainModelGateway([groq, cerebras, mistral])

    result = await chain.generate(_req())

    assert groq.calls == 1
    assert cerebras.calls == 1
    assert mistral.calls == 0
    assert result.text == "z cerebras"
    assert result.provider_metadata["provider"] == "cerebras"


@pytest.mark.asyncio
async def test_last_gateway_used_when_all_previous_fail():
    groq = StubGateway("groq", error=RuntimeError("groq down"))
    cerebras = StubGateway("cerebras", error=RuntimeError("cerebras down"))
    mistral = StubGateway("mistral", text="z mistral")
    chain = ChainModelGateway([groq, cerebras, mistral])

    result = await chain.generate(_req())

    assert result.text == "z mistral"
    assert result.provider_metadata["provider"] == "mistral"


@pytest.mark.asyncio
async def test_all_failed_raises_last_error():
    groq = StubGateway("groq", error=RuntimeError("groq down"))
    cerebras = StubGateway("cerebras", error=RuntimeError("cerebras down"))
    mistral = StubGateway("mistral", error=RuntimeError("mistral down"))
    chain = ChainModelGateway([groq, cerebras, mistral])

    with pytest.raises(RuntimeError, match="mistral down"):
        await chain.generate(_req())


class StreamStubGateway(ModelGateway):
    def __init__(
        self, name: str, *, error: Exception | None = None, chunks: list[str] | None = None
    ):
        self._name = name
        self._error = error
        self._chunks = chunks or []
        self.calls = 0

    def provider_name(self) -> str:
        return self._name

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return ModelResponse(
            request_id=request.request_id,
            text="ok",
            finish_reason="stop",
            tool_calls=(),
            provider_metadata={"provider": self._name},
        )

    async def stream(self, request: ModelRequest):
        self.calls += 1
        if self._error is not None:
            raise self._error
        for c in self._chunks:
            yield c


@pytest.mark.asyncio
async def test_stream_first_gateway_wins_when_ok():
    groq = StreamStubGateway("groq", chunks=["a", "b"])
    cerebras = StreamStubGateway("cerebras", chunks=["x"])
    chain = ChainModelGateway([groq, cerebras])
    out = []
    async for c in chain.stream(_req()):
        out.append(c)
    assert out == ["a", "b"]
    assert groq.calls == 1
    assert cerebras.calls == 0


@pytest.mark.asyncio
async def test_stream_falls_back_to_next_if_first_fails_before_yield():
    groq = StreamStubGateway("groq", error=RuntimeError("fail"))
    cerebras = StreamStubGateway("cerebras", chunks=["hi"])
    chain = ChainModelGateway([groq, cerebras])
    out = []
    async for c in chain.stream(_req()):
        out.append(c)
    assert out == ["hi"]
    assert groq.calls == 1
    assert cerebras.calls == 1


@pytest.mark.asyncio
async def test_stream_does_not_switch_after_partial_yield():
    class PartialError(StreamStubGateway):
        async def stream(self, request: ModelRequest):
            self.calls += 1
            yield "hello"
            raise RuntimeError("mid-stream")

    groq = PartialError("groq", chunks=[])
    cerebras = StreamStubGateway("cerebras", chunks=["world"])
    chain = ChainModelGateway([groq, cerebras])
    out = []
    with pytest.raises(RuntimeError, match="mid-stream"):
        async for c in chain.stream(_req()):
            out.append(c)
    assert out == ["hello"]
    assert cerebras.calls == 0


@pytest.mark.asyncio
async def test_stream_all_failed_raises_last_error():
    groq = StreamStubGateway("groq", error=RuntimeError("g"))
    cerebras = StreamStubGateway("cerebras", error=RuntimeError("c"))
    chain = ChainModelGateway([groq, cerebras])
    with pytest.raises(RuntimeError, match="c"):
        async for _ in chain.stream(_req()):
            pass
