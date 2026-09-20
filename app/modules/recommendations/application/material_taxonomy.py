"""Material families for matching. Codes follow EWC-style chapter prefixes."""

FAMILIES = {
    "bio": {
        "aliases": {"bio", "kompost", "organic", "organicke", "biowaste"},
        "ewc_prefixes": ("20 01 08", "20 02 01", "02"),
    },
    "drevo": {
        "aliases": {"drevo", "wood", "piliny", "pilovina", "piloviny"},
        "ewc_prefixes": ("03 01", "15 01 03", "17 02 01"),
    },
    "kov": {
        "aliases": {"kov", "zelezo", "železo", "metal", "spony", "ocel", "oceľ"},
        "ewc_prefixes": ("17 04", "16 01 17", "12 01"),
    },
    "pet": {
        "aliases": {"pet", "plast", "plastove", "granule", "plastic"},
        "ewc_prefixes": ("15 01 02", "20 01 39", "12 01 05", "07 02"),
    },
    "papier": {
        "aliases": {"papier", "paper", "karton", "lepenka"},
        "ewc_prefixes": ("15 01 01", "20 01 01", "03 03"),
    },
    "stavebne": {
        "aliases": {"stavebne", "sut", "suť", "beton", "betón", "construction"},
        "ewc_prefixes": ("17 01", "17 03", "17 05", "17 08", "17 09"),
    },
    "sklo": {
        "aliases": {"sklo", "glass"},
        "ewc_prefixes": ("15 01 07", "17 02 02", "20 01 02"),
    },
    "textil": {
        "aliases": {"textil", "textile", "odev"},
        "ewc_prefixes": ("04 02", "20 01 10", "20 01 11"),
    },
    "olej": {
        "aliases": {"olej", "oil", "mazivo"},
        "ewc_prefixes": ("13"),
    },
    "eeo": {
        "aliases": {"eeo", "weee", "elektro", "elektroodpad"},
        "ewc_prefixes": ("16 02", "20 01 21", "20 01 23", "20 01 35", "20 01 36"),
    },
}


HAZARDOUS_PREFIXES = ("13", "14", "16 02", "20 01 21", "20 01 23", "20 01 35")


def _norm(value: str) -> str:
    return " ".join(value.casefold().replace(";", " ").replace(",", " ").replace("-", " ").split())


def _spaced_ewc(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) == 6:
        return digits[0:2] + " " + digits[2:4] + " " + digits[4:6]
    if len(digits) == 4:
        return digits[0:2] + " " + digits[2:4]
    if len(digits) == 2:
        return digits
    return ""


def expand_material(raw: str | None) -> set[str]:
    text = _norm(raw or "")
    if not text:
        return set()
    spaced = _spaced_ewc(text)
    if spaced:
        text = spaced
    out: set[str] = set()
    ranked: list[tuple[int, str, str]] = []
    for family, spec in FAMILIES.items():
        for prefix in spec["ewc_prefixes"]:
            ranked.append((len(_norm(prefix)), _norm(prefix), family))
    ranked.sort(reverse=True)
    for _length, prefix, family in ranked:
        if text == prefix or text.startswith(prefix + " "):
            out.add(family)
            out |= {item.casefold() for item in FAMILIES[family]["aliases"]}
            break
    tokens = {part for part in text.split(" ") if part and not part.isdigit()}
    out |= tokens
    for token in list(tokens):
        for family, spec in FAMILIES.items():
            aliases = {item.casefold() for item in spec["aliases"]}
            if token in aliases or any(
                len(alias) >= 4 and (token.startswith(alias) or alias.startswith(token))
                for alias in aliases
            ):
                out.add(family)
                out |= aliases
    for prefix in HAZARDOUS_PREFIXES:
        if text == prefix or text.startswith(prefix + " "):
            out.add("hazardous")
            break
    return out
