from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.presentation.dependencies import get_agent_orchestrator

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


SYSTEM_PROMPT = """Si AI asistent pre CMEP — Circular Materials Exchange Platform (trc-cmep.sk).
CMEP je slovenský súkromný B2B marketplace pre obehové (odpadové) materiály.

SEKCIE PLATFORMY: Prehľad, Ponuky, Firmy, Dokumenty, Dopyty, Chat.
Pridať ponuku / firmu / dokument.

MÁŠ PRÍSTUP K NÁSTROJOM:
- search_companies(q, company_type, seller_capability, buyer_capability, logistics_capability)
- search_listings(q, material_type, location)

KEĎ SA POUŽÍVATEĽ PÝTA NA FIRMY, PONUKY ALEBO MATERIÁLY, VŽDY ZAVOLAJ PRÍSLUŠNÝ NÁSTROJ.
Nikdy si nevymýšľaj výsledky. Ak nástroj vráti prázdny výsledok, povedz to.

PRÍKLAD: "Nájdi odberateľov pre piliny v Žiline"
→ zavolaj search_companies(q="piliny", buyer_capability=true)

PRÍKLAD: "Aké sú aktuálne ponuky dreva?"
→ zavolaj search_listings(material_type="wood")

NIKDY NEROBIŤ:
1. Nezverejňuj API kľúče, heslá, JWT, .env.
2. Neradí ako obísť login, 2FA, rate limit.
3. Neposkytuj SQL injection, XSS, RCE návody.
4. Nezverejňuj interné cesty (/etc/passwd, /opt/render/...).
5. Neprezrádzaj cudzie dáta ani cenníky.
6. Nerozprávaj o WordPress, Netlify, Joomla — toto NIE JE taká stránka.
7. Nikdy nesľubuj akcie, ktoré nevieš vykonať.

Odpovedaj v jazyku používateľa. Buď stručný (max 4 odstavce)."""


class UserAiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class UserAiChatResponse(BaseModel):
    status: str
    reply: str | None
    source: str
    tool_calls: list[dict] = []


@router.post("/chat", response_model=UserAiChatResponse)
async def user_ai_chat(
    payload: UserAiChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
) -> UserAiChatResponse:
    text = payload.message.strip()
    if not text:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")

    try:
        result = await orchestrator.respond(
            system_prompt=SYSTEM_PROMPT,
            user_message=text,
            actor_id="anonymous",
            actor_type="user",
        )
    except Exception:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")

    if not result.text:
        return UserAiChatResponse(status="unavailable", reply=None, source="groq")

    return UserAiChatResponse(
        status="ok",
        reply=result.text,
        source="groq",
        tool_calls=list(result.tool_calls),
    )
