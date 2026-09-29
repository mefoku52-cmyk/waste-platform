from fastapi import APIRouter, Depends

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


from pydantic import BaseModel as _BaseModel

from app.modules.agent_platform.application.control.control_service import (
    DefaultControlService,
)
from app.modules.agent_platform.application.control.emergency_service import (
    DefaultEmergencyService,
)
from app.modules.agent_platform.domain.control.control_action import (
    ControlAction,
)
from app.modules.agent_platform.infrastructure.persistence.control_repository import (
    SqlAlchemyControlRepository,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_admin
from app.shared.presentation.authorization import current_user_id


class _ModeChangeRequest(_BaseModel):
    action: str
    reason: str = ""


@router.get("/mode")
async def get_control_mode(
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
) -> dict:
    svc = DefaultControlService(repository=SqlAlchemyControlRepository(session))
    mode = await svc.get_mode()
    return {"mode": mode.value}


@router.post("/mode")
async def change_control_mode(
    payload: _ModeChangeRequest,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
) -> dict:
    from fastapi import HTTPException

    try:
        action = ControlAction(payload.action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Unknown action: {payload.action}") from exc
    svc = DefaultControlService(repository=SqlAlchemyControlRepository(session))
    actor = current_user_id(current_user) or "admin"
    new_mode = await svc.apply(action, actor, payload.reason or action.value)
    return {"mode": new_mode.value, "actor": actor}


@router.post("/emergency/activate")
async def emergency_activate(
    payload: _ModeChangeRequest,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
) -> dict:
    svc = DefaultEmergencyService(repository=SqlAlchemyControlRepository(session))
    actor = current_user_id(current_user) or "admin"
    state = await svc.activate(actor, payload.reason or "manual activation")
    return {"mode": state.mode.value, "changedBy": state.changed_by}


@router.post("/emergency/release")
async def emergency_release(
    payload: _ModeChangeRequest,
    current_user=Depends(require_admin),
    session=Depends(get_db_session),
) -> dict:
    svc = DefaultEmergencyService(repository=SqlAlchemyControlRepository(session))
    actor = current_user_id(current_user) or "admin"
    state = await svc.release(actor, payload.reason or "manual release")
    return {"mode": state.mode.value, "changedBy": state.changed_by}
