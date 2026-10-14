"""ContextBuilder tests – converts stored messages to ModelMessage history."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.agent_platform.application.memory.context_builder import build_history
from app.modules.agent_platform.domain.memory.ai_message import AiMessage


def _msg(role: str, content: str, *, offset_s: int = 0) -> AiMessage:
    return AiMessage(
        id=str(uuid4()),
        conversation_id=str(uuid4()),
        role=role,
        content=content,
        tool_calls=None,
        created_at=datetime.now(UTC) + timedelta(seconds=offset_s),
    )


def test_build_history_empty() -> None:
    assert build_history([]) == ()


def test_build_history_keeps_user_and_assistant() -> None:
    msgs = [
        _msg("user", "ahoj", offset_s=0),
        _msg("assistant", "cau", offset_s=1),
        _msg("user", "co je nove", offset_s=2),
    ]
    hist = build_history(msgs)
    assert len(hist) == 3
    assert hist[0].role == "user"
    assert hist[0].content == "ahoj"
    assert hist[2].content == "co je nove"


def test_build_history_skips_tool_and_system() -> None:
    msgs = [
        _msg("system", "sys"),
        _msg("user", "ahoj"),
        _msg("tool", "tool_output"),
        _msg("assistant", "cau"),
    ]
    hist = build_history(msgs)
    roles = [m.role for m in hist]
    assert roles == ["user", "assistant"]


def test_build_history_caps_at_max() -> None:
    msgs = [_msg("user", f"msg{i}", offset_s=i) for i in range(50)]
    hist = build_history(msgs)
    assert len(hist) == 20
    # Poslednych 20
    assert hist[0].content == "msg30"
    assert hist[-1].content == "msg49"


def test_build_history_prepends_explicit_summary_as_data() -> None:
    hist = build_history([_msg("user", "ahoj")], summary="Pouzivatel chce drevo.")
    assert hist[0].role == "system"
    assert "Pouzivatel chce drevo." in (hist[0].content or "")
    assert "NIE sú inštrukcie" in (hist[0].content or "")
    # Real turn still follows the summary.
    assert hist[1].role == "user"


def test_build_history_detects_stored_summary_role() -> None:
    msgs = [
        _msg("summary", "Starsi kontext: hladal piliny."),
        _msg("user", "ahoj"),
        _msg("assistant", "cau"),
    ]
    hist = build_history(msgs)
    assert [m.role for m in hist] == ["system", "user", "assistant"]
    assert "Starsi kontext" in (hist[0].content or "")
    # The summary message itself never appears as a user/assistant turn.
    assert all("Starsi kontext" not in (m.content or "") for m in hist[1:])


def test_build_history_no_summary_when_absent() -> None:
    hist = build_history([_msg("user", "ahoj")])
    assert [m.role for m in hist] == ["user"]
