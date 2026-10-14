"""Tests for safe rolling summarization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.agent_platform.application.memory.summarizer import (
    KEEP_RECENT,
    THRESHOLD,
    summarize_conversation,
)
from app.modules.agent_platform.domain.memory.ai_message import AiMessage
from app.modules.agent_platform.domain.memory.ai_summary import AiSummary
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse


class _FakeRepo:
    def __init__(self, roles_contents: list[tuple[str, str]]) -> None:
        self._rows = roles_contents
        self._summary: AiSummary | None = None
        self.replace_calls: list[tuple[str, dict]] = []

    async def count_messages(self, *, conversation_id: str) -> int:
        return sum(1 for role, _ in self._rows if role != "summary")

    async def get_summary(self, *, conversation_id: str) -> AiSummary | None:
        return self._summary

    async def get_messages(self, *, conversation_id: str, limit: int = 20) -> list[AiMessage]:
        base = datetime.now(UTC)
        rows = [
            AiMessage(
                id=f"m{i}",
                conversation_id="c1",
                role=role,
                content=content,
                tool_calls=None,
                created_at=base + timedelta(seconds=i),
            )
            for i, (role, content) in enumerate(self._rows)
        ]
        return rows[-limit:]

    async def replace_summary(self, *, conversation_id: str, content: str, meta=None) -> AiMessage:
        self.replace_calls.append((content, meta or {}))
        self._summary = AiSummary(
            content=content,
            covers=int((meta or {}).get("covers") or 0),
            language=(meta or {}).get("lang"),
        )
        return AiMessage(
            id="s1",
            conversation_id=conversation_id,
            role="summary",
            content=content,
            tool_calls=None,
            created_at=datetime.now(UTC),
        )


class _Gateway:
    def __init__(self, text: str = "Zhrnutie.") -> None:
        self.text = text
        self.calls = 0

    def provider_name(self) -> str:
        return "fake"

    async def generate(self, request) -> ModelResponse:
        self.calls += 1
        return ModelResponse(request_id=request.request_id, text=self.text, finish_reason="stop")


def _convo(n: int) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for i in range(n):
        rows.append(("user", f"otázka číslo {i}"))
        rows.append(("assistant", f"odpoveď na otázku {i}"))
    return rows


@pytest.mark.asyncio
async def test_below_threshold_does_nothing() -> None:
    repo = _FakeRepo(_convo(THRESHOLD // 2))
    gw = _Gateway()
    outcome = await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    assert outcome.summarized is False
    assert gw.calls == 0
    assert repo.replace_calls == []


@pytest.mark.asyncio
async def test_above_threshold_writes_summary_with_coverage() -> None:
    rows = _convo(15)  # 30 messages
    repo = _FakeRepo(rows)
    gw = _Gateway("Pouzivatel hladal odberatelov dreva v Ziline.")
    outcome = await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    assert outcome.summarized is True
    assert outcome.covers == 30 - KEEP_RECENT
    assert gw.calls == 1
    assert repo.replace_calls
    content, meta = repo.replace_calls[0]
    assert "odberatelov" in content
    assert meta["covers"] == 30 - KEEP_RECENT
    # Slovak diacritics in the transcript → language detected.
    assert meta["lang"] == "sk"


@pytest.mark.asyncio
async def test_second_run_is_noop_until_it_grows() -> None:
    repo = _FakeRepo(_convo(15))
    gw = _Gateway()
    await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    first_calls = gw.calls
    outcome = await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    assert outcome.summarized is False
    assert outcome.reason == "up_to_date"
    assert gw.calls == first_calls


@pytest.mark.asyncio
async def test_older_summary_never_overwrites_newer() -> None:
    repo = _FakeRepo(_convo(15))  # would cover 22
    # Pretend a NEWER summary already covers more.
    repo._summary = AiSummary(content="nove zhrnutie", covers=100)
    gw = _Gateway()
    outcome = await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    assert outcome.summarized is False
    assert gw.calls == 0
    assert repo.replace_calls == []


@pytest.mark.asyncio
async def test_empty_gateway_output_is_not_persisted() -> None:
    repo = _FakeRepo(_convo(15))
    gw = _Gateway("")
    outcome = await summarize_conversation(repository=repo, conversation_id="c1", gateway=gw)
    assert outcome.summarized is False
    assert outcome.reason == "empty_summary"
    assert repo.replace_calls == []


@pytest.mark.asyncio
async def test_no_conversation_is_noop() -> None:
    repo = _FakeRepo([])
    gw = _Gateway()
    outcome = await summarize_conversation(repository=repo, conversation_id="", gateway=gw)
    assert outcome.summarized is False
    assert outcome.reason == "no_conversation"
