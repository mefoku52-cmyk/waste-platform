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

import logging
import os
from dataclasses import dataclass

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.model_request import (
    ModelMessage,
    ModelRequest,
)
from app.modules.agent_platform.infrastructure.ai.model_response import ModelResponse

logger = logging.getLogger(__name__)

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


# Deterministicke casti, ktore MUSIA byt v kazdom emaili — aj v AI verzii,
# aj vo fallbacku bez AI. Drzime ich na jednom mieste, aby sa nerozisli.
_STOP_LINE = "Ak nemáte záujem, odpovedzte prosím slovom STOP a už Vás nikdy nekontaktujeme."

_GDPR_FOOTER = (
    "Vaše kontaktné údaje sme získali z verejného registra RPO "
    "(Štatistický úrad SR). Spracúvame ich na základe oprávneného "
    "záujmu podľa čl. 6 ods. 1 písm. f) GDPR. Máte právo namietať, "
    "požiadať o výmaz alebo prístup k údajom. Kontakt: trc-cmep@gmail.com"
)

_SIGNATURE = "S pozdravom,\nRadoslav Cornanič\nCMEP — trc-cmep.sk\ntrc-cmep@gmail.com"

_EARLY_BIRD_LINE = (
    "Prvých 10 firiem registrovaných na platforme získa PRO alebo AI "
    "verziu ZADARMO navždy — aktuálne je ešte pár miest voľných."
)


def _fallback_draft(
    *,
    company_name: str,
    city: str | None = None,
    industry: str | None = None,
    early_bird: bool = False,
) -> DraftedEmail:
    """Deterministický návrh emailu bez AI.

    Používa VÝLUČNE fakty, ktoré už máme z RPO: názov firmy, mesto a
    odvetvie. Nič nedomýšľa — žiadne čísla, zľavy, referencie ani
    tvrdenia o firme, ktoré by sme nevedeli doložiť.

    GDPR blok, STOP veta a podpis sú identické s AI verziou.
    """
    name = company_name.strip()
    subject = f"Pozvánka na CMEP pre {name}"

    where: list[str] = []
    if city and city.strip():
        where.append(f"v lokalite {city.strip()}")
    if industry and industry.strip():
        where.append(f"v oblasti {industry.strip()}")

    if where:
        reason = (
            "Oslovujeme Vás, pretože CMEP je trhovisko s obehovými "
            f"materiálmi a druhotnými surovinami a firmy {' a '.join(where)} "
            "môžu na ňom inzerovať alebo hľadať materiály."
        )
    else:
        reason = (
            "Oslovujeme Vás, pretože CMEP je trhovisko s obehovými "
            "materiálmi a druhotnými surovinami."
        )

    blocks: list[str] = [
        "Dobrý deň,",
        "",
        reason,
        "",
        "Registrácia je dobrovoľná, bez viazanosti a bez provízií. "
        "Inzerovať aj hľadať môžete hneď po registrácii.",
        "",
    ]

    if early_bird:
        blocks.extend([_EARLY_BIRD_LINE, ""])

    blocks.extend(
        [
            _STOP_LINE,
            "",
            _SIGNATURE,
            "",
            "---",
            _GDPR_FOOTER,
        ]
    )

    return DraftedEmail(subject=subject, body="\n".join(blocks))


class EmailDrafter:
    def __init__(self, *, gateway: GroqModelGateway | None = None) -> None:
        self._gateway = gateway or GroqModelGateway()

    @staticmethod
    def is_provider_configured() -> bool:
        """True, ak je AI provider nakonfigurovany (bez odhalenia kluce).

        Pouziva to /admin/lead-outreach/status. Vracia len bool — hodnota
        kluca sa nikdy nevracia ani neloguje.
        """
        return bool(os.getenv("GROQ_API_KEY", "").strip())

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

        # Ak AI provider nie je nakonfigurovany alebo zlyha (timeout, 5xx,
        # vycerpany kvota), draft NESMIE spadnut — admin musi dostat
        # pouzitelny email. Fallback je deterministicky a pouziva len
        # company_name/city/industry.
        try:
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
        except Exception as exc:
            logger.warning(
                "AI draft zlyhal (%s: %s) — pouzivam deterministicky fallback",
                type(exc).__name__,
                exc,
            )
            return _fallback_draft(
                company_name=company_name,
                city=city,
                industry=industry,
                early_bird=early_bird,
            )

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
        # AI vratila prazdne telo — pouzi rovnaky deterministicky fallback
        # ako pri zlyhani providera, aby GDPR blok a STOP boli vzdy pritomne.
        return _fallback_draft(company_name=fallback_company)

    return DraftedEmail(subject=subject, body=body)
