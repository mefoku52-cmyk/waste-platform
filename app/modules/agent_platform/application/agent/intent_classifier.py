"""Rule-based intent classifier for the CMEP chat agent.

This is the FIRST, deterministic layer of intent detection. It never authorizes
anything and never calls a tool — it only decides which *area* the user is
talking about so the orchestrator can be nudged with a short hint and the UI can
react. Authorization stays on the server, in the tool handlers.

Design notes:

* Matching is diacritic-insensitive and case-insensitive, so ``predám``,
  ``predam`` and ``PREDÁM`` all hit the same stem. Common typos fall out of the
  same normalisation.
* Keywords are *stems* with a word-start boundary, so ``ponuk`` covers
  ``ponuka / ponuky / ponuku`` without matching ``ponukaX`` inside another word.
  Very short tokens (``hi``) require a full word boundary on both sides.
* The classifier is deliberately conservative: when nothing matches it returns
  ``unknown`` (not a risky default), and when the top two intents tie it flags
  ``ambiguous`` so the agent asks a clarifying question instead of guessing.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    SEARCH = "search"
    SELL = "sell"
    NAVIGATE = "navigate"
    FORM_HELP = "form_help"
    RECOMMENDATION = "recommendation"
    INQUIRY = "inquiry"
    PLATFORM_HELP = "platform_help"
    UNKNOWN = "unknown"


# Tie-break priority — when two intents score the same, the earlier one wins.
# The order favours concrete, low-risk, action-oriented intents over small talk.
_PRIORITY: tuple[Intent, ...] = (
    Intent.FORM_HELP,
    Intent.NAVIGATE,
    Intent.SELL,
    Intent.INQUIRY,
    Intent.RECOMMENDATION,
    Intent.SEARCH,
    Intent.GREETING,
    Intent.PLATFORM_HELP,
)

# Stems per intent (normalised: lower-case, no diacritics).
_KEYWORDS: dict[Intent, tuple[str, ...]] = {
    Intent.GREETING: (
        "ahoj",
        "ahojte",
        "cau",
        "cauko",
        "servus",
        "nazdar",
        "zdravim",
        "zdar",
        "dobry den",
        "dobre rano",
        "dobry vecer",
        "hello",
        "hi",
        "hey",
    ),
    Intent.SELL: (
        "predam",
        "predavam",
        "predat",
        "predaj",
        "predav",
        "ponukam",
        "na predaj",
        "chcem predat",
    ),
    Intent.SEARCH: (
        "najdi",
        "najde",
        "najst",
        "hladam",
        "hladat",
        "vyhlad",
        "odberatel",
        "kupc",
        "kupuj",
        "kto kup",
        "kto odober",
    ),
    Intent.NAVIGATE: (
        "otvor",
        "ukaz",
        "zobraz",
        "zoznam",
        "moje ponuk",
        "moju ponuk",
        "moje dopyt",
        "moje firm",
        "moju firm",
        "pridat ponuk",
        "pridat firm",
        "pridat dokument",
        "nova ponuk",
        "novu ponuk",
        "novu firm",
        "vrat",
        "spat na",
        "dashboard",
        "prejdi",
        "chod na",
        "nastaven",
        "formular",
    ),
    Intent.FORM_HELP: (
        "vypln",
        "vyplnit",
        "dopln",
        "predvypln",
        "pomoz vyplnit",
        "pomoc s formular",
        "pomoz s formular",
    ),
    Intent.RECOMMENDATION: (
        "odporuc",
        "podobn",
        "co k tomu",
        "komu predat",
        "komu to",
        "co odporucas",
        "kto by to kupil",
        "kto by kup",
    ),
    Intent.INQUIRY: (
        "dopyt",
        "poslat dopyt",
        "poslem dopyt",
        "mam zaujem",
        "zaujem o",
        "kontaktovat",
        "chcem oslovit",
    ),
    Intent.PLATFORM_HELP: (
        "ako funguje",
        "ako to funguje",
        "co je cmep",
        "co je trc",
        "co je platforma",
        "ako pridat",
        "ako predam",
        "vysvetli",
        "navod",
        "napoveda",
        "s cim vies",
        "co vies",
        "co dokazes",
    ),
}

_SHORT_TOKEN_LEN = 3


@dataclass(frozen=True, slots=True)
class IntentResult:
    intent: Intent
    confidence: float
    ambiguous: bool
    scores: Mapping[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "ambiguous": self.ambiguous,
        }


def _normalize(text: str) -> str:
    """Lower-case and strip diacritics so Slovak variants match one stem."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return ascii_only.lower()


def _pattern(stem: str) -> re.Pattern[str]:
    escaped = re.escape(stem)
    if len(stem) <= _SHORT_TOKEN_LEN:
        # Whole word only — avoids "hi" matching "historia".
        return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
    # Word-start boundary + optional inflection suffix (ponuk → ponuky).
    return re.compile(rf"(?<![a-z0-9]){escaped}[a-z]*")


_PATTERNS: dict[Intent, tuple[re.Pattern[str], ...]] = {
    intent: tuple(_pattern(stem) for stem in stems) for intent, stems in _KEYWORDS.items()
}


def classify_intent(text: str) -> IntentResult:
    """Return the most likely intent for a user message.

    Pure and side-effect free; safe to call on untrusted input. Scores are the
    number of distinct keyword stems matched per intent.
    """
    norm = _normalize(text)
    if not norm.strip():
        return IntentResult(Intent.UNKNOWN, 0.0, False, {})

    scores: dict[Intent, int] = {}
    for intent, patterns in _PATTERNS.items():
        hits = sum(1 for pat in patterns if pat.search(norm))
        if hits:
            scores[intent] = hits

    if not scores:
        return IntentResult(Intent.UNKNOWN, 0.0, False, {})

    best_score = max(scores.values())
    top = [i for i, s in scores.items() if s == best_score]
    ambiguous = len(top) > 1
    # Deterministic winner via the fixed priority order.
    winner = next(
        (i for i in _PRIORITY if i in top),
        min(top, key=lambda i: i.value),
    )
    confidence = min(1.0, 0.5 + 0.15 * best_score)
    return IntentResult(
        intent=winner,
        confidence=confidence,
        ambiguous=ambiguous,
        scores={i.value: s for i, s in scores.items()},
    )


def intent_hint(result: IntentResult) -> str:
    """Short, non-authoritative hint appended to the system prompt.

    It only tells the model where the user's message most likely points and —
    when the signal is weak/ambiguous — to ask instead of acting. It grants no
    capability and overrides no server rule.
    """
    if result.intent is Intent.UNKNOWN and not result.ambiguous:
        return (
            "\n\nODHAD ZAMERU: neisty. Ak poziadavka nie je jasna, opytaj sa "
            "pouzivatela jednou vetou namiesto toho, aby si nieco spustil."
        )

    label = {
        Intent.GREETING: "pozdrav — odpovedz kratko a priatelsky, nic nespustaj",
        Intent.SEARCH: "hladanie — pouzi vyhladavaci nastroj a vysledky ukaz ako karty",
        Intent.SELL: "predaj — otvor formular novej ponuky a pomoz s polami",
        Intent.NAVIGATE: "navigacia — otvor existujucu internu stranku CMEP",
        Intent.FORM_HELP: "pomoc s formularom — pouzi fill_form_field / highlight_field",
        Intent.RECOMMENDATION: ("odporucanie — vyjdi z kontextu aktualnej entity a najdi podobne"),
        Intent.INQUIRY: "dopyt — najdi firmu a priprav dopyt, NIKDY ho neodosli sam",
        Intent.PLATFORM_HELP: "pomoc s platformou — vysvetli funkciu strucne",
        Intent.UNKNOWN: "neisty",
    }.get(result.intent, "neisty")

    hint = f"\n\nODHAD ZAMERU (nepovinny, neriesi opravnenia): {label}."
    if result.ambiguous:
        hint += (
            " Signal je nejednoznacny — radsej sa najprv opytaj alebo ponukni "
            "2-3 moznosti, nez aby si hladal/vykonaval naslepo."
        )
    return hint
