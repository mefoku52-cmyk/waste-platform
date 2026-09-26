"""Context builder – converts stored AI messages to LLM history."""

from __future__ import annotations

from app.modules.agent_platform.domain.memory.ai_message import AiMessage
from app.modules.agent_platform.infrastructure.ai.model_request import ModelMessage

MAX_HISTORY_MESSAGES = 20


def build_history(messages: list[AiMessage]) -> tuple[ModelMessage, ...]:
    """Return chronological ModelMessage history from stored messages.

    Tool and system roles are skipped – LLM continuity only needs
    user/assistant turns. Empty content is dropped.
    """
    out: list[ModelMessage] = []
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        role = m.role
        if role not in ("user", "assistant"):
            continue
        content = (m.content or "").strip()
        if not content:
            continue
        out.append(ModelMessage(role=role, content=content))
    return tuple(out)
