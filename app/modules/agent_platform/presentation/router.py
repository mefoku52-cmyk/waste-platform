from fastapi import APIRouter

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


@router.get("/health")
async def agent_platform_health() -> dict[str, object]:
    """Informational health for the agent platform.

    chat=True     – chat_router is mounted and requires authentication.
    control=False – control_router exposes status only; no live commands.
    """
    return {
        "status": "present",
        "wired": True,
        "chat": True,
        "control": False,
    }
