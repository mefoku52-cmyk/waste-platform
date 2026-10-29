"""Bridge - realna AI logika pre navigatora s FALLBACKOM."""
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
from app.modules.agent_platform.navigator.fallback_adapter import FallbackAdapter

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
        
        # 1. Vytvorime adaptéry - citame z Environment premenných!
        adapters = {}
        
        # GROQ - hlavny model (pouzije GROQ_MODEL z Renderu, inak default)
        if os.environ.get("GROQ_API_KEY"):
            adapters["groq"] = GenericAPIAdapter(
                name="groq",
                api_url="https://api.groq.com/openai/v1/chat/completions",
                api_key_env="GROQ_API_KEY",
                model_name=os.environ.get("GROQ_MODEL", "llama3-8b-8192"),
                policy=self._policy,
            )
            
        # CEREBRAS - fallback 1 (pouzije CEREBRAS_MODEL z Renderu)
        if os.environ.get("CEREBRAS_API_KEY"):
            adapters["cerebras"] = GenericAPIAdapter(
                name="cerebras",
                api_url=os.environ.get("CEREBRAS_API_URL", "https://api.cerebras.ai/v1/chat/completions"),
                api_key_env="CEREBRAS_API_KEY",
                model_name=os.environ.get("CEREBRAS_MODEL", "llama3.1-8b"),
                policy=self._policy,
            )
            
        # MISTRAL - fallback 2 (pouzije MISTRAL_MODEL z Renderu)
        if os.environ.get("MISTRAL_API_KEY"):
            adapters["mistral"] = GenericAPIAdapter(
                name="mistral",
                api_url="https://api.mistral.ai/v1/chat/completions",
                api_key_env="MISTRAL_API_KEY",
                model_name=os.environ.get("MISTRAL_MODEL", "mistral-small-latest"),
                policy=self._policy,
            )

        # 2. Zapojime ich do FallbackAdapteru
        if adapters:
            self._adapter = FallbackAdapter(adapters=adapters, policy=self._policy)
            _log.info(f"Navigator inicializovany s modelmi: {list(adapters.keys())}")
        else:
            self._adapter = None
            _log.error("ZIADNY API KLUC NEBOL NAJDENY! Navigator nebude fungovat.")

    async def respond(
        self, system_prompt: str, user_message: str, actor_id: str, actor_type: str,
        session_id: str, conversation_history: tuple = (), old_orchestrator: Any = None,
    ) -> Any:
        try:
            assignment = self._intake.accept(title=user_message[:100], description=user_message)
            
            ai_prompt = (
                f"Si inteligentny AI asistent pre platformu CMEP.\n"
                f"Pouzivatel sa pyta: '{user_message}'\n\n"
                "MAS DVE MOZNOSTI ODPOVEDE:\n"
                "1. AK CHCE NAVIGOVAT (otvorit firmu, chat, dopyty, prehlad), odpovedz IBA ako JSON: {\"action\": \"open_companies\"} (alebo open_chat, open_inquiries, open_dashboard).\n"
                "2. AK SA PYTA NA NIEČO INÉ, odpovedz NORMALNYM TEXTom (ziadny JSON)."
            )
            
            if not self._adapter:
                reply = "CHYBA: Na serveri nie su nastavene API kluce (Cerebras, Mistral alebo Groq)."
            else:
                response = self._adapter.infer(ai_prompt)
                action = None
                
                if not response.available:
                    reply = f"Chyba AI: {response.error}."
                elif not response.result:
                    reply = "AI nevrátila žiadnu odpoveď."
                else:
                    raw_text = response.result.strip()
                    try:
                        clean_result = raw_text.replace("```json", "").replace("```", "").strip()
                        if clean_result.startswith("{") and clean_result.endswith("}"):
                            data = json.loads(clean_result)
                            action = data.get("action")
                            if action:
                                reply = f"Otvaram... ({action})"
                            else:
                                reply = "Rozumiem, ale neviem aku akciu mam vykonat."
                        else:
                            reply = raw_text
                    except Exception:
                        reply = raw_text

            return {
                "status": "ok",
                "reply": reply,
                "source": "navigator",
                "session_id": session_id,
                "action": action,
                "tasks": [t.id for t in assignment.tasks],
            }
            
        except Exception as exc:
            _log.exception("NAVIGATOR: exception: %s", exc)
            if old_orchestrator is not None:
                return await old_orchestrator.respond(
                    system_prompt=system_prompt, user_message=user_message,
                    actor_id=actor_id, actor_type=actor_type, session_id=session_id,
                    conversation_history=conversation_history,
                )
            return {"status": "unavailable", "reply": f"Chyba: {type(exc).__name__}", "source": "navigator"}

_bridge_instance: NavigatorBridge | None = None

def get_navigator_bridge() -> NavigatorBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NavigatorBridge()
    return _bridge_instance
