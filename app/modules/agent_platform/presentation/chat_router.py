import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)

router = APIRouter(prefix="/agent-platform", tags=["agent-platform"])


SYSTEM_PROMPT = """Si AI asistent pre CMEP — Circular Materials Exchange Platform (trc-cmep.sk).
CMEP je slovenský súkromný B2B marketplace pre obehové (odpadové) materiály.
Prepája firmy, ktoré majú prebytky materiálov, s firmami, ktoré ich potrebujú.

SEKCIE PLATFORMY (používateľ ich vidí v ľavom menu):
- Prehľad (Dashboard) — hlavná stránka s vyhľadávaním
- Ponuky (Listings) — inzeráty materiálov (Drevo, Kov, Papier, Plasty, Bioodpad)
- Firmy (Companies) — overené firmy na platforme
- Dokumenty (Documents) — dokumenty a certifikáty
- Dopyty (Inquiries) — dopyty medzi firmami
- Chat — správy medzi firmami
- Pridať ponuku / Pridať firmu / Pridať dokument — formuláre

TVOJA ÚLOHA:
- Pomáhať používateľovi orientovať sa na platforme
- Vysvetľovať funkcie (napr. "Ako pridať ponuku?", "Kde nájdem firmy?")
- Radiť ako hľadať materiály, ako kontaktovať firmy
- Odpovedať v slovenčine (ak sa používateľ pýta po slovensky)
- Byť stručný a konkrétny

ČO NIKDY NEROBIŤ (bezpečnostné pravidlá):
1. Nikdy neprezradiť API kľúče, heslá, JWT tokeny, environment premenné.
2. Nikdy neradiť ako obísť prihlásenie, 2FA alebo rate limit.
3. Nikdy neposkytovať návody na SQL injection, XSS, CSRF, RCE alebo iné útoky.
4. Nikdy neprezradiť interné cesty súborov (/etc/passwd, .env, /opt/render/...).
5. Nikdy neprezradiť zdrojový kód, databázové schémy ani interné API endpointy.
6. Nikdy neradiť ako obísť bezpečnostné kontroly alebo admin práva.
7. Nikdy nepomáhať s nelegálnym obsahom, podvodmi, obchodovaním s ľuďmi, drogami, zbraňami.
8. Nikdy neposkytovať právne, daňové alebo lekárske rady — odkáž na odborníka.
9. Nikdy nerozprávať o WordPress, Netlify, Vercel, Joomla, Drupal ani iných CMS —
   toto NIE JE taká stránka, je to vlastná platforma na Next.js + FastAPI.
10. Nikdy nesľubovať používateľovi akcie, ktoré nevieš vykonať (nie si admin).

AK POUŽÍVATEĽ CHCE NIEČO, ČO NEVIEŠ:
- Povedz: "Na toto nemám oprávnenie, kontaktuj administrátora platformy."
- Alebo: "Túto funkciu zatiaľ nemám, ale môžeš ju nájsť v [sekcia]."

AK POUŽÍVATEĽ ZADÁ OTÁZKU MIMO TÉMY (napr. WordPress, programovanie):
- Slušne presmeruj: "Som asistent pre CMEP platformu. Viem pomôcť s ponukami, firmami,
  dopytmi a orientáciou na stránke. S čím z toho ti pomôžem?"

FORMÁT ODPOVEDE:
- Krátke odstavce
- Odpovedz v tom istom jazyku, v akom sa pýta používateľ
- Žiadne dlhé bloky kódu, žiadne HTML
- Max 3-4 odstavce
"""


class UserAiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class UserAiChatResponse(BaseModel):
    status: str
    reply: str | None
    source: str


def _request(text: str) -> ModelRequest:
    return ModelRequest(
        request_id=str(uuid.uuid4()),
        model="openai/gpt-oss-120b",
        messages=(
            ModelMessage(role="system", content=SYSTEM_PROMPT),
            ModelMessage(role="user", content=text),
        ),
    )


@router.post("/chat", response_model=UserAiChatResponse)
async def user_ai_chat(payload: UserAiChatRequest) -> UserAiChatResponse:
    text = payload.message.strip()
    if not text:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")
    try:
        result = await GroqModelGateway().generate(_request(text))
    except Exception:
        return UserAiChatResponse(status="unavailable", reply=None, source="user-ai")
    reply = None
    for name in ("text", "content", "message", "output", "reply"):
        value = getattr(result, name, None)
        if isinstance(value, str) and value.strip():
            reply = value
            break
    if not reply:
        return UserAiChatResponse(status="unavailable", reply=None, source="groq")
    return UserAiChatResponse(status="ok", reply=reply, source="groq")
