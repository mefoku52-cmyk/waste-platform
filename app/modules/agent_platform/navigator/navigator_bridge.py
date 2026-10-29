"""Bridge - realna AI logika pre navigatora."""
from __future__ import annotations
import os
import json
import logging
from typing import Any

from app.modules.agent_platform.navigator.task_intake import TaskIntake
from app.modules.agent_platform.navigator.task_coordinator import TaskCoordinator
from app.modules.agent_platform.navigator.execution_policy import ExecutionPolicy, ExecutionMode
from app.modules.agent_platform.navigator.agent_roles import AgentRoleManager, Agent, AgentRole
from app.modules.agent_platform.navigator.generic_api_adapter import GenericAPIAdapter

_log = logging.getLogger("cmep.navigator.bridge")

class NavigatorBridge:
    def __init__(self):
        self._intake = TaskIntake()
        self._policy = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
        self._role_manager = AgentRoleManager()
        self._role_manager.register_agent(Agent(name="navigator", role=AgentRole.COORDINATOR))
        self._coordinator = TaskCoordinator(
            policy=self._policy, role_manager=self._role_manager, max_attempts=1, default_timeout=10.0
        )
        # Inicializacia Cerebras modelu z .env
        self._adapter = GenericAPIAdapter(
            name="cerebras",
            api_url=os.environ.get("CEREBRAS_API_URL", "https://api.cerebras.ai/v1/chat/completions"),
            api_key_env="CEREBRAS_API_KEY",
            model_name=os.environ.get("CEREBRAS_MODEL", "llama3.1-8b"),
            policy=self._policy,
        )

    async def respond(
        self, system_prompt: str, user_message: str, actor_id: str, actor_type: str,
        session_id: str, conversation_history: tuple = (), old_orchestrator: Any = None,
    ) -> Any:
        try:
            assignment = self._intake.accept(title=user_message[:100], description=user_message)
            
            # REALNA AI LOGIKA - posleme to modelu
            ai_prompt = (
                f"Si AI navigator pre platformu CMEP. Pouzivatel napisal: '{user_message}'.\n"
                "Tvojou ulohou je rozhodnut, ktoru akciu treba vykonat. Mas na vyber z tychto akcii:\n"
                "- open_companies (otvorit zoznam firiem)\n"
                "- open_chat (otvorit chat)\n"
                "- open_inquiries (otvorit dopyty)\n"
                "- open_dashboard (otvorit prehlad)\n"
                "Ak si nie si isty, vrat action: null.\n"
                "Odpovedz IBA ako JSON, napriklad: {\"action\": \"open_companies\"}"
            )
            
            response = self._adapter.infer(ai_prompt)
            action = None
            reply = "Rozumiem. Spracuvavam tvoj prikaz."
            
            if response.available and response.result:
                try:
                    # Ocistime odpoved od pripadnych markdown blokov
                    clean_result = response.result.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_result)
                    action = data.get("action")
                    if action:
                        reply = f"Otvaram... ({action})"
                except Exception as e:
                    _log.warning(f"AI neposlala validny JSON: {response.result}")

            return {
                "status": "ok",
                "reply": reply,
                "source": "navigator",
                "session_id": session_id,
                "action": action,
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
