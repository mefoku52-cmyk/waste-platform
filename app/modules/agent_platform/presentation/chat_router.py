from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.presentation.dependencies import (
    get_agent_orchestrator,
    get_company_entitlement_service,
)
from app.modules.companies.application.entitlements import CompanyEntitlementService
from app.modules.companies.domain.enums import SubscriptionTier
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
)

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


async def _check_ai_entitlement(
    *,
    current_user,
    entitlements: CompanyEntitlementService,
) -> None:
    """Raise 402/403 if the caller is not entitled to AI chat.

    Platform admins always pass.
    Company members with PRO or AI tier pass.
    FREE tier returns 402 Payment Required.
    Members without a company return 403 Forbidden.
    """
    if is_platform_admin(current_user):
        return

    company_ids = membership_company_ids(current_user)
    if not company_ids:
        raise HTTPException(
            status_code=403,
            detail="Najprv si vytvor a over firmu (AI asistent vyžaduje firemný účet).",
        )

    for cid in company_ids:
        if await entitlements.has_tier(cid, SubscriptionTier.PRO):
            return

    raise HTTPException(
        status_code=402,
        detail="AI asistent je dostupný v PRO alebo AI predplatnom.",
    )


@router.post("/chat", response_model=UserAiChatResponse)
async def user_ai_chat(
    payload: UserAiChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
    current_user=Depends(require_current_user),
    entitlements: CompanyEntitlementService = Depends(get_company_entitlement_service),
) -> UserAiChatResponse:
    text = payload.message.strip()
    if not text:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")

    await _check_ai_entitlement(
        current_user=current_user,
        entitlements=entitlements,
    )

    try:
        result = await orchestrator.respond(
            system_prompt=SYSTEM_PROMPT,
            user_message=text,
            actor_id=str(getattr(current_user, "id", "unknown")),
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
