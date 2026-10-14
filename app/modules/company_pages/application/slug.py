"""Slug helpers for public company pages.

Bez externej závislosti (``python-slugify`` bol z projektu odstránený).
Normalizácia diakritiky cez ``unicodedata`` NFKD → ASCII, takže slovenské
znaky (á, č, š, ž, ľ, ť, ď, ň, ô, …) sa korektne prevedú na ASCII ekvivalenty.
"""

from __future__ import annotations

import re
import unicodedata

SLUG_MIN_LENGTH = 3
SLUG_MAX_LENGTH = 80

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slugify(value: str | None) -> str:
    """Prevedie ľubovoľný text na URL-bezpečný slug (bez diakritiky)."""
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only)
    ascii_only = re.sub(r"-{2,}", "-", ascii_only).strip("-")
    return ascii_only[:SLUG_MAX_LENGTH].strip("-")


def is_valid_slug(slug: str | None) -> bool:
    """Serverová validácia tvaru slug-u (nie unikátnosti)."""
    if not slug:
        return False
    if not (SLUG_MIN_LENGTH <= len(slug) <= SLUG_MAX_LENGTH):
        return False
    return bool(_SLUG_RE.match(slug))


def unique_slug(base: str, existing: list[str], *, max_attempts: int = 200) -> str:
    """Vráti unikátny slug vzhľadom na ``existing``.

    Pri kolízii pridá numerický suffix (``-2``, ``-3`` …). DB unique
    constraint ostáva konečnou poistkou proti súbehu; tento helper je len
    pohodlná predvoľba pre používateľa.
    """
    taken = {s for s in existing if s}
    candidate = base or "firma"
    if candidate not in taken:
        return candidate
    for i in range(2, max_attempts + 2):
        suffix = f"-{i}"
        trimmed = candidate[: SLUG_MAX_LENGTH - len(suffix)].rstrip("-")
        proposal = f"{trimmed}{suffix}"
        if proposal not in taken:
            return proposal
    return candidate
