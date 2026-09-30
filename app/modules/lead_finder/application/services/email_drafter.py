"""AI email drafter pre B2B oslovenie firiem.

GDPR-kompatibilny B2B cold email. Nikdy neposiela automaticky.
Kazdy email schvaluje admin manualne.

Pravny zaklad:
- GDPR (Nariadenie EU 2016/679), clanok 6 ods. 1 pism. f) — opravneny zaujem
- Zakon c. 452/2021 Z. z. o elektronickych komunikaciach, § 116
  (B2B oslovenie pravnickej osoby je mozne, ak su splnene podmienky)

Kazdy email obsahuje:
1. Identifikaciu odosielatela (meno, kontakt)
2. Ucel spracuvania
3. Pravny zaklad
4. Zdroj udajov (odkial mame email)
5. Jasny opt-out (STOP)
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

_SYSTEM = """Si asistent pre CMEP (trc-cmep.sk) — slovensky B2B marketplace
s obehovymi materialmi. Tvojou ulohou je napisat kratky, slusny,
personalizovany B2B email pre firmu, ktoru chceme pozvat na platformu.

PRAVNY RAMEC (MUSIS DODRZAT):
- GDPR (Nariadenie EU 2016/679), clanok 6 ods. 1 pism. f) — opravneny zaujem
- Zakon c. 452/2021 Z. z. o elektronickych komunikaciach, § 116
- Email je urceny VYLUCNE pravnickej osobe (firme), nikdy nie fyzickej osobe

PRAVIDLA PRE OBSAH:
1. Email v slovencine, 90-130 slov (nie viac).
2. Nikdy neslubuj konkretne cisla, zlavy ani partnerstva, ktore neexistuju.
3. Vzdy uved jasny, konkretny dovod, preco pises prave tejto firme
   (napr. "firma spracuva drevo a mohla by mat zaujem o predaj pilin").
4. Ziaden HTML. Len plain text. Ziadne emoji.
5. Ziadne marketingove frazy typu "revolucny", "unikatny", "najlepsi",
   "revolucia", "game-changer".
6. Podpis (presne takto):
   Radoslav Cornanic
   CMEP — trc-cmep.sk
   trc-cmep@gmail.com

PRAVIDLA PRE GDPR BLOK (POVINNE NA KONCI):
Za podpisom pridaj presne tieto 4 riadky (nic viac, nic menej):

---
Vase kontaktne udaje sme ziskali z verejneho registra RPO
(Statisticky urad SR). Spracuvame ich na zaklade opravneneho zaujmu
podla cl. 6 ods. 1 pism. f) GDPR. Mate pravo namietat, poziadat
o vymaz alebo pristup k udajom. Kontakt: trc-cmep@gmail.com

PRAVIDLA PRE OPT-OUT (POVINNE):
Pred podpisom vzdy pridaj tuto vetu (presne takto):
"Ak nemate zaujem, odpovedzte prosim slovom STOP a uz Vas nikdy
nekontaktujeme."

PRAVIDLA PRE EARLY BIRD:
- AK ti pouzivatel povie, ze EARLY BIRD je AKTIVNY, pridaj presne tuto vetu:
  "Prvych 10 firiem registrovanych na platforme ziska PRO alebo AI verziu
  ZADARMO navzdy — aktualne je este par miest volnych."
- AK early bird NIE JE aktivny, tuto vetu NIKDY nepridavaj.
- Nikdy nespominaj zlavy, bonusy ani PRO verzie, ak early bird nie je aktivny.

FORMAT ODPOVEDE — vrat presne dve casti oddelene tromi pomlckami:

SUBJECT: <predmet emailu>
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
        early_bird: bool = False,
    ) -> DraftedEmail:
        parts: list[str] = [f"Nazov firmy: {company_name.strip()}"]
        if city and city.strip():
            parts.append(f"Mesto: {city.strip()}")
        if industry and industry.strip():
            parts.append(f"Odvetvie: {industry.strip()}")
        if reason and reason.strip():
            parts.append(f"Dovod kontaktovania: {reason.strip()}")
        if early_bird:
            parts.append(
                "EARLY BIRD PONUKA JE AKTIVNA: ano "
                "(prvych 10 firiem na platforme ziska PRO/AI zadarmo navzdy, "
                "este je volnych miest)."
            )
        else:
            parts.append("EARLY BIRD PONUKA JE AKTIVNA: nie")

        prompt = "\n".join(parts) + "\n\nNapíš email presne podľa pravidiel."

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
            "Dobry den,\n\n"
            "dovolujem si Vas kontaktovat ohladom CMEP — trhoviska s obehovymi "
            "materialmi.\n"
            "Ak nemate zaujem, odpovedzte prosim slovom STOP a uz Vas nikdy "
            "nekontaktujeme.\n\n"
            "S pozdravom,\n"
            "Radoslav Cornanic\n"
            "CMEP — trc-cmep.sk\n"
            "trc-cmep@gmail.com\n\n"
            "---\n"
            "Vase kontaktne udaje sme ziskali z verejneho registra RPO "
            "(Statisticky urad SR). Spracuvame ich na zaklade opravneneho "
            "zaujmu podla cl. 6 ods. 1 pism. f) GDPR. Mate pravo namietat, "
            "poziadat o vymaz alebo pristup k udajom. Kontakt: trc-cmep@gmail.com"
        )

    return DraftedEmail(subject=subject, body=body)
