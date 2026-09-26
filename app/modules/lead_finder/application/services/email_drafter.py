"""AI email drafter for B2B outreach.

Strictly legal B2B cold email. Never auto-sends. Never loops over lists.
One draft at a time, admin approves each send.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

_SYSTEM = """Si asistent pre CMEP (trc-cmep.sk) — slovenský B2B marketplace s obehovými materiálmi.
Tvojou úlohou je napísať krátky, slušný, personalizovaný B2B email pre firmu,
ktorú chceme pozvať na platformu.

PRAVIDLÁ:
1. Email musí byť v slovenčine, maximálne 120 slov.
2. Nikdy nesľubuj konkrétne čísla, zľavy alebo partnerstvá, ktoré neexistujú.
3. Vždy uveď jasný dôvod, prečo píšeme (napr. firma podniká v odvetví, ktoré súvisí s materiálmi).
4. Vždy pridaj vetu s možnosťou odhlásenia: "Ak nemáte záujem, odpovedzte prosím slovom STOP a už Vás nikdy nekontaktujeme."
5. Žiadne emoji. Žiadne marketingové frázy typu "revolučný", "unikátny", "najlepší".
6. Podpis: "Radoslav Čornanič, CMEP — trc-cmep.sk"
7. Žiadny HTML. Len plain text.
8. Neuvádzaj moje telefónne číslo ani adresu.

Vráť presne dve časti oddelené prázdnym riadkom:
SUBJECT: <predmet>
---
<telo emailu>
"""


@dataclass(frozen=True, slots=True)
class DraftedEmail:
    subject: str
    body: str


class EmailDrafter:
    def __init__(self, *, gateway: GroqModelGateway | None = None) -> None:
        self._gateway = gateway or GroqModelGateway()

    async def draft(
        self,
        *,
        company_name: str,
        city: str | None = None,
        industry: str | None = None,
        reason: str | None = None,
    ) -> DraftedEmail:
        parts: list[str] = [f"Názov firmy: {company_name.strip()}"]
        if city and city.strip():
            parts.append(f"Mesto: {city.strip()}")
        if industry and industry.strip():
            parts.append(f"Odvetvie: {industry.strip()}")
        if reason and reason.strip():
            parts.append(f"Dôvod kontaktovania: {reason.strip()}")

        prompt = "\n".join(parts) + "\n\nNapíš email podľa pravidiel."

        response: ModelResponse = await self._gateway.generate(
            ModelRequest(
                request_id="lead-draft",
                model="openai/gpt-oss-120b",
                messages=(
                    ModelMessage(role="system", content=_SYSTEM),
                    ModelMessage(role="user", content=prompt),
                ),
                temperature=0.4,
            )
        )
        text = (response.text or "").strip()
        return _parse_draft(text, fallback_company=company_name)


def _parse_draft(text: str, *, fallback_company: str) -> DraftedEmail:
    subject = f"Pozvánka na CMEP pre {fallback_company}"
    body = text

    if text.upper().startswith("SUBJECT:"):
        lines = text.split("\n", 1)
        first = lines[0]
        rest = lines[1] if len(lines) > 1 else ""
        subj_val = first.split(":", 1)[1].strip()
        if subj_val:
            subject = subj_val
        body = rest.split("---", 1)[1].strip() if "---" in rest else rest.strip()

    if not body:
        body = (
            "Dobrý deň,\n\n"
            "dovoľujem si Vás kontaktovať ohľadom CMEP — trhoviska s obehovými materiálmi.\n"
            "Ak nemáte záujem, odpovedzte prosím slovom STOP a už Vás nikdy nekontaktujeme.\n\n"
            "S pozdravom,\nRadoslav Čornanič\nCMEP — trc-cmep.sk"
        )

    return DraftedEmail(subject=subject, body=body)
