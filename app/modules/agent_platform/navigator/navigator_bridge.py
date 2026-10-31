"""Bridge - realna AI logika pre navigatora s FALLBACKOM a dynamickym zoznamom stranok."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from app.modules.agent_platform.navigator.agent_roles import Agent, AgentRole, AgentRoleManager
from app.modules.agent_platform.navigator.execution_policy import ExecutionMode, ExecutionPolicy
from app.modules.agent_platform.navigator.fallback_adapter import FallbackAdapter
from app.modules.agent_platform.navigator.generic_api_adapter import GenericAPIAdapter
from app.modules.agent_platform.navigator.task_coordinator import TaskCoordinator
from app.modules.agent_platform.navigator.task_intake import TaskIntake

_log = logging.getLogger("cmep.navigator.bridge")

# Stranky, ktore vie navigator otvorit.
# KLUCE musia existovat vo frontende (NO_ARG_NAV_ACTIONS v ai-chat-widget.tsx)
NAV_PAGES = {
    "open_dashboard": ("dashboard", "prehlad, domov, uvodna stranka"),
    "open_listings_list": ("zoznam ponúk", "ponuky, trhovisko, moje ponuky"),
    "open_new_listing": ("formulár novej ponuky", "pridat alebo vytvorit novu ponuku"),
    "open_companies": ("zoznam firiem", "firmy"),
    "open_new_company": ("formulár novej firmy", "pridat alebo vytvorit novu firmu"),
    "open_documents": ("zoznam dokumentov", "dokumenty, zmluvy, certifikaty"),
    "open_new_document": ("formulár nového dokumentu", "pridat alebo nahrat novy dokument"),
    "open_inquiries": ("dopyty", "dopyty, otazky k ponukam"),
    "open_chat": ("chat", "spravy medzi firmami"),
    "open_settings": ("nastavenia", "nastavenia, bezpecnost, heslo"),
    "open_transport": ("prepravcovia", "prepravcovia, doprava, logistika"),
    "open_subscription": ("predplatné", "predplatne, cennik, tarify, plan"),
    "open_marketplace": ("marketplace", "vsetky ponuky, trh, marketplace"),
}


def build_nav_prompt(user_message: str) -> str:
    pages = [
        "- " + action + ": " + label + " (" + hint + ")"
        for action, (label, hint) in NAV_PAGES.items()
    ]
    return (
        "Si inteligentny asistent platformy CMEP.\n"
        "Pouzivatel napisal: '" + user_message[:500] + "'\n\n"
        "Stranky, ktore vies otvorit (a ich akcie):\n" + "\n".join(pages) + "\n\n"
        "PRAVIDLA:\n"
        "1. Ak pouzivatel chce otvorit niektoru z tychto stranok, odpovedz IBA JSON-om "
        'v tvare {"action": "nazov_akcie"} a nic ine. Pouzi presne jeden nazov zo zoznamu.\n'
        "2. Ak chce stranku, ktora v zozname nie je (napr. predplatne, prepravcovia), "
        "alebo sa pyta na nieco ine, odpovedz normalnym textom bez JSON. "
        "Nikdy nevymyslaj nazov akcie.\n"
        "Nikdy nevyberaj platený plán ani nespúšťaj platbu; môžeš iba otvoriť stránku predplatného."
    )


def nav_reply(action: str) -> str:
    return "Otváram: " + NAV_PAGES[action][0] + "."


class NavigatorBridge:
    def __init__(self):
        self._intake = TaskIntake()
        self._policy = ExecutionPolicy(mode=ExecutionMode.DRY_RUN)
        self._role_manager = AgentRoleManager()
        self._role_manager.register_agent(Agent(name="navigator", role=AgentRole.COORDINATOR))
        self._coordinator = TaskCoordinator(
            policy=self._policy, role_manager=self._role_manager, max_attempts=1, default_timeout=10
        )

        adapters = {}

        # GROQ - hlavny model
        if os.environ.get("GROQ_API_KEY"):
            adapters["groq"] = GenericAPIAdapter(
                name="groq", api_url="https://api.groq.com/openai/v1/chat/completions",
                api_key_env="GROQ_API_KEY",
                model_name=os.environ.get("GROQ_MODEL", "llama3-8b-8192"),
                policy=self._policy,
            )

        # CEREBRAS - fallback 1
        if os.environ.get("CEREBRAS_API_KEY"):
            adapters["cerebras"] = GenericAPIAdapter(
                name="cerebras", api_url=os.environ.get("CEREBRAS_API_URL", "https://api.cerebras.ai/v1/chat/completions"),
                api_key_env="CEREBRAS_API_KEY",
                model_name=os.environ.get("CEREBRAS_MODEL", "llama3.1-8b"),
                policy=self._policy,
            )

        # MISTRAL - fallback 2
        if os.environ.get("MISTRAL_API_KEY"):
            adapters["mistral"] = GenericAPIAdapter(
                name="mistral", api_url="https://api.mistral.ai/v1/chat/completions",
                api_key_env="MISTRAL_API_KEY",
                model_name=os.environ.get("MISTRAL_MODEL", "mistral-small-latest"),
                policy=self._policy,
            )

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

            history_text = ""
            if conversation_history:
                history_text = "Predchadzajuca konverzacia:\n" + "\n".join([f"{m.role}: {m.content}" for m in conversation_history[-3:]]) + "\n\n"

            ai_prompt = history_text + build_nav_prompt(user_message)

            if not self._adapter:
                reply = "CHYBA: Na serveri nie su nastavene API kluce."
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

                            # Podpora pre jednu akciu alebo zoznam akcii
                            if "actions" in data and isinstance(data["actions"], list):
                                valid_actions = [a for a in data["actions"] if a in NAV_PAGES]
                                if valid_actions:
                                    reply = "Otváram: " + ", ".join([NAV_PAGES[a][0] for a in valid_actions]) + "."
                                    action = valid_actions # Posleme zoznam
                                else:
                                    reply = raw_text
                            elif "action" in data and isinstance(data["action"], str) and data["action"] in NAV_PAGES:
                                action = data["action"]
                                reply = nav_reply(action)
                            else:
                                action = None
                                reply = raw_text # Alebo "Tuto stranku neviem otvorit."
                        else:
                            reply = raw_text
                    except Exception:
                        reply = raw_text

            return {
                "status": "ok", "reply": reply, "source": "navigator",
                "session_id": session_id, "action": action if isinstance(action, list) else ([action] if action else []), "tasks": [t.id for t in assignment.tasks],
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
