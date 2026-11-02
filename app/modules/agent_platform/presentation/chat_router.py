"""Chat router pre /agent-platform/chat.

Historicky tu žila duplicitná implementácia, ktorá sa rozišla s
``user_ai_chat_router.py`` a nakoniec ostala prázdna (iba importy a prázdny
router) — endpoint ``POST /agent-platform/chat`` teda neexistoval a frontend
dostával 405. Jediná udržiavaná implementácia je ``user_ai_chat_router.py``;
tento modul ju re-exportuje, aby mount v ``api_router.py`` ostal nedotknutý.
"""

from __future__ import annotations

from app.modules.agent_platform.presentation.user_ai_chat_router import (
    BASE_RULES,
    _build_page_context_block,
    _build_system_prompt,
    _check_ai_entitlement,
    _detect_security_patterns,
    router,
)

__all__ = [
    "BASE_RULES",
    "_build_page_context_block",
    "_build_system_prompt",
    "_check_ai_entitlement",
    "_detect_security_patterns",
    "router",
]
