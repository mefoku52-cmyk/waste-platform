from fastapi import APIRouter

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


@router.get("/health")
async def agent_platform_health() -> dict[str, object]:
    return {
        "status": "present",
        "wired": True,
        "chat": False,
        "control": False,
    }
