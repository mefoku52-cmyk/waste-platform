"""AI listing drafter — vygeneruje návrh ponuky z promptu.

Pattern: rovnaký ako lead_finder/email_drafter.py.
Vyžaduje AI tier firmy (kontrola v router.py, nie tu).

Fallback (bez AI): deterministický návrh z promptu.
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
s obehovymi materialmi. Tvojou ulohou je z kratkeho popisu od uzivatela
vytvorit strukturovany navrh ponuky (listing).

PRAVIDLA:
1. Vypln vsetky polia maximalne strucne a realisticky.
2. Nepridavaj cisla, ceny ani tvrdenia, ktore uzivatel nespomenul.
3. Ak nieco chyba, daj null.
4. Jazyk: rovnaky ako v prompte (sk/cz/en/de/ru/fr).
5. Odpovedaj IBA validnym JSON (ziadny text okolo).

FORMAT JSON:
{
  "title": "kratky nazov ponuky (max 80 znakov)",
  "description": "2-3 vety popisu materialu, stav, moznosti odberu",
  "materialType": "typ materialu (drevo/kov/papier/plasty/bioodpad/ine)",
  "quantity": cislo alebo null,
  "unit": "kg/t/m3/kus" alebo null,
  "location": "mesto alebo null",
  "condition": "nove/pouzite/odpad" alebo null,
  "currency": "EUR" alebo null,
  "price": cislo alebo null
}
"""


@dataclass(frozen=True, slots=True)
class DraftedListing:
    title: str
    description: str
    materialType: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    condition: str | None = None
    currency: str | None = None
    price: float | None = None


def _fallback_from_prompt(prompt: str) -> DraftedListing:
    """Deterministický návrh z promptu — bez AI.

    Používa iba to, čo user napísal. Nič nedomýšľa.
    """
    text = prompt.strip()
    title = text[:80] if text else "Nová ponuka"
    return DraftedListing(
        title=title,
        description=text if text else "Popis ponuky",
        materialType=None,
        quantity=None,
        unit=None,
        location=None,
        condition=None,
        currency="EUR",
        price=None,
    )


class ListingDrafter:
    def __init__(self, *, gateway: GroqModelGateway | None = None) -> None:
        self._gateway = gateway or GroqModelGateway()

    @staticmethod
    def is_provider_configured() -> bool:
        return bool(os.getenv("GROQ_API_KEY", "").strip())

    async def draft(self, *, prompt: str) -> DraftedListing:
        try:
            response: ModelResponse = await self._gateway.generate(
                ModelRequest(
                    request_id="listing-draft",
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
                "AI listing draft zlyhal (%s: %s) — fallback",
                type(exc).__name__,
                exc,
            )
            return _fallback_from_prompt(prompt)

        return _parse_draft(text, prompt)


def _parse_draft(text: str, prompt: str) -> DraftedListing:
    import json
    import re

    # AI môže obaliť JSON do ```json ... ``` — vyčisti
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except (ValueError, TypeError):
        logger.warning("AI vrátilo neplatný JSON — fallback z promptu")
        return _fallback_from_prompt(prompt)

    def _str(key: str) -> str | None:
        v = data.get(key)
        return str(v).strip() if v else None

    def _num(key: str) -> float | None:
        v = data.get(key)
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    title = _str("title") or prompt[:80] or "Nová ponuka"
    description = _str("description") or prompt or "Popis ponuky"

    return DraftedListing(
        title=title[:80],
        description=description,
        materialType=_str("materialType"),
        quantity=_num("quantity"),
        unit=_str("unit"),
        location=_str("location"),
        condition=_str("condition"),
        currency=_str("currency") or "EUR",
        price=_num("price"),
    )
