from fastapi import APIRouter

router = APIRouter(prefix="/agent-platform/control", tags=["agent-platform-control"])


@router.get("/status")
async def control_status() -> dict[str, object]:
    return {
        "status": "present",
        "actor": "radoslav",
        "approval": False,
        "break_glass": False,
        "live": False,
    }


@router.get("/health")
async def control_health() -> dict[str, object]:
    return {
        "status": "present",
        "wired": True,
        "commands": False,
    }
