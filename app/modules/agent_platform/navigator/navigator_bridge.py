"""Bridge medzi starym AgentOrchestrator a novym TaskCoordinator."""

from __future__ import annotations
import logging
from typing import Any

from app.modules.agent_platform.navigator.task_intake import TaskIntake
from app.modules.agent_platform.navigator.task_coordinator import TaskCoordinator
from app.modules.agent_platform.navigator.execution_policy import ExecutionPolicy, ExecutionMode
from app.modules.agent_platform.navigator.agent_roles import AgentRoleManager, Agent, AgentRole

_log = logging.getLogger("cmep.navigator.bridge")

class NavigatorBridge:
    def __init__(self):
        self._intake = TaskIntake()
        self._policy = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
        self._role_manager = AgentRoleManager()
        self._role_manager.register_agent(Agent(name="navigator", role=AgentRole.COORDINATOR))
        self._coordinator = TaskCoordinator(
            policy=self._policy,
            role_manager=self._role_manager,
            max_attempts=1,
            default_timeout=10.0,
        )

    async def respond(
        self,
        system_prompt: str,
        user_message: str,
        actor_id: str,
        actor_type: str,
        session_id: str,
        conversation_history: tuple = (),
        old_orchestrator: Any = None,
    ) -> Any:
        try:
            # 1. Rozloz zadanie
            assignment = self._intake.accept(title=user_message[:100], description=user_message)
            
            # 2. Zisti, ci mame spravit nejaku akciu (jednoduchy keyword matching)
            msg = user_message.lower()
            action = None
            reply = f"Navigator rozlozil zadanie na {len(assignment.tasks)} uloh a vsetky presli suchym behom."
            
            if "firm" in msg or "firmy" in msg:
                action = "open_companies"
                reply = "Otvaram zoznam firiem..."
            elif "chat" in msg:
                action = "open_chat"
                reply = "Otvaram chat..."
            elif "dopyt" in msg or "dopyty" in msg:
                action = "open_inquiries"
                reply = "Otvaram dopyty..."
            elif "dashboard" in msg or "prehlad" in msg:
                action = "open_dashboard"
                reply = "Otvaram dashboard..."
                
            return {
                "status": "ok",
                "reply": reply,
                "source": "navigator",
                "session_id": session_id,
                "action": action,  # Posielame akciu frontendu!
                "tasks": [t.id for t in assignment.tasks],
            }
        except Exception as exc:
            _log.exception("NAVIGATOR: exception, skusam stary orchestrator: %s", exc)
            if old_orchestrator is not None:
                return await old_orchestrator.respond(
                    system_prompt=system_prompt, user_message=user_message,
                    actor_id=actor_id, actor_type=actor_type, session_id=session_id,
                    conversation_history=conversation_history,
                )
            return {"status": "unavailable", "reply": "Chyba navigatora.", "source": "navigator"}

_bridge_instance: NavigatorBridge | None = None

def get_navigator_bridge() -> NavigatorBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NavigatorBridge()
    return _bridge_instance
