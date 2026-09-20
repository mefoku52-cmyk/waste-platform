"""Material families for matching. Codes follow EWC-style chapter prefixes."""

FAMILIES = {
    "bio": {
        "aliases": {"bio", "kompost", "organic", "organicke", "biowaste"},
        "ewc_prefixes": ("02", "20 01 08", "20 02 01"),
    },
    "drevo": {
        "aliases": {"drevo", "wood", "piliny", "pilovina", "piloviny"},
        "ewc_prefixes": ("03 01", "15 01 03", "17 02 01"),
    },
    "kov": {
        "aliases": {"kov", "zelezo", "železo", "metal", "spony", "ocel", "oceľ"},
        "ewc_prefixes": ("12 01", "16 01 17", "17 04"),
    },
    "pet": {
        "aliases": {"pet", "plast", "plastove", "granule", "plastic"},
        "ewc_prefixes": ("07 02", "12 01 05", "15 01 02", "20 01 39"),
    },
    "papier": {
        "aliases": {"papier", "paper", "karton", "lepenka"},
        "ewc_prefixes": ("03 03", "15 01 01", "20 01 01"),
    },
    "stavebne": {
        "aliases": {"stavebne", "sut", "suť", "beton", "betón", "construction"},
        "ewc_prefixes": ("17",),
    },
}


def _norm(value: str) -> str:
    return " ".join(value.casefold().replace(";", " ").replace(",", " ").split())


def expand_material(raw: str | None) -> set[str]:
    tokens = {part for part in _norm(raw or "").split(" ") if part}
    out = set(tokens)
    for token in list(tokens):
        for family, spec in FAMILIES.items():
            aliases = {item.casefold() for item in spec["aliases"]}
            prefixes = spec["ewc_prefixes"]
            if token in aliases or any(
                _norm(token).startswith(_norm(prefix)) for prefix in prefixes
            ):
                out.add(family)
                out |= aliases
    return out
