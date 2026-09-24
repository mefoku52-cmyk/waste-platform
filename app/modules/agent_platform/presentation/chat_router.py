import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


class UserAiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class UserAiChatResponse(BaseModel):
    status: str
    reply: str | None
    source: str


def _request(text: str) -> ModelRequest:
    return ModelRequest(
        request_id=str(uuid.uuid4()),
        model="llama-3.1-8b-instant",
        messages=(ModelMessage(role="user", content=text),),
    )


@router.post("/chat", response_model=UserAiChatResponse)
async def user_ai_chat(payload: UserAiChatRequest) -> UserAiChatResponse:
    text = payload.message.strip()
    if not text:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")
    try:
        result = await GroqModelGateway().generate(_request(text))
    except Exception:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")
    reply = None
    for name in ("text", "content", "message", "output", "reply"):
        value = getattr(result, name, None)
        if isinstance(value, str) and value.strip():
            reply = value
            break
    if not reply:
        return UserAiChatResponse(status="unavailable", reply=None, source="groq")
    return UserAiChatResponse(status="ok", reply=reply, source="groq")
