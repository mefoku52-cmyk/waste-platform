"""Bridge medzi starym AgentOrchestrator a novym TaskCoordinator.

Priorita:
1. TaskCoordinator (novy navigator) - primarny
2. AgentOrchestrator (stary mozog) - fallback

Ak novy navigator zlyha, pouzije sa stary.
"""

from __future__ import annotations

import logging
from typing import Any

from app.modules.agent_platform.navigator.agent_roles import Agent, AgentRole, AgentRoleManager
from app.modules.agent_platform.navigator.execution_policy import ExecutionMode, ExecutionPolicy
from app.modules.agent_platform.navigator.task_coordinator import TaskCoordinator
from app.modules.agent_platform.navigator.task_intake import TaskIntake

_log = logging.getLogger("cmep.navigator.bridge")


class NavigatorBridge:
    """Prepojenie medzi starym a novym systemom."""

    def __init__(self):
        self._intake = TaskIntake()
        self._policy = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
        self._role_manager = AgentRoleManager()
        self._role_manager.register_agent(Agent(name="navigator", role=AgentRole.COORDINATOR))
        self._coordinator = TaskCoordinator(
            policy=self._policy,
            role_manager=self._role_manager,
            max_attempts=2,
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
        """Skusi novy navigator, ak zlyha, pouzije stary orchestrator."""
        try:
            # 1. Rozloz zadanie na ulohy
            assignment = self._intake.accept(
                title=user_message[:100],
                description=user_message,
            )

            _log.info(
                "NAVIGATOR: rozlozene na %d uloh pre actor=%s",
                len(assignment.tasks),
                actor_id,
            )

            # 2. Vykonaj kazdu ulohu (suchy beh)
            results = []
            for task in assignment.tasks:
                result = self._coordinator.run(
                    task_id=task.id,
                    func=lambda t=task: f"[NAVIGATOR] {t.title}",
                    agent_name="navigator",
                    operation="diagnose",
                )
                results.append(result)

            # 3. Ak vsetko preslo, vrat odpoved
            if all(r.status == "completed" for r in results):
                return {
                    "status": "ok",
                    "reply": f"Navigator rozlozil zadanie na {len(results)} uloh a vsetky presli suchym behom.",
                    "source": "navigator",
                    "session_id": session_id,
                    "tasks": [r.task_id for r in results],
                }

            # Ak nieco zlyhalo, skus stary orchestrator
            _log.warning("NAVIGATOR: niektore ulohy zlyhali, skusam stary orchestrator")

        except Exception as exc:
            _log.exception("NAVIGATOR: exception, skusam stary orchestrator: %s", exc)

        # Fallback na stary orchestrator
        if old_orchestrator is not None:
            return await old_orchestrator.respond(
                system_prompt=system_prompt,
                user_message=user_message,
                actor_id=actor_id,
                actor_type=actor_type,
                session_id=session_id,
                conversation_history=conversation_history,
            )

        return {
            "status": "unavailable",
            "reply": None,
            "source": "navigator",
            "session_id": session_id,
        }


# Globalna instancia (singleton)
_bridge_instance: NavigatorBridge | None = None


def get_navigator_bridge() -> NavigatorBridge:
    """Vrati globalnu instanciu bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NavigatorBridge()
    return _bridge_instance
