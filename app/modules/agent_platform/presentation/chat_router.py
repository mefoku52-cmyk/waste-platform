from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


class UserAiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class UserAiChatResponse(BaseModel):
    status: str
    reply: str | None
    source: str


@router.post("/chat", response_model=UserAiChatResponse)
async def user_ai_chat(payload: UserAiChatRequest) -> UserAiChatResponse:
    if not payload.message.strip():
        return UserAiChatResponse(
            status="unavailable",
            reply=None,
            source="user-ai",
        )
    return UserAiChatResponse(
        status="unavailable",
        reply=None,
        source="user-ai",
    )
