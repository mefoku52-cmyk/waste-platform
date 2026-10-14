#!/usr/bin/env bash
set -Eeuo pipefail

# Spustiť z koreňa repozitára Waste Platform.
# Skript nemení databázu, nerobí git reset, commit ani push.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

FILES=(
  "tests/unit/test_company_services.py"
  "tests/unit/test_listings_service.py"
)
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR=".repair-backup-$STAMP"
mkdir -p "$BACKUP_DIR"

for file in "${FILES[@]}"; do
  test -f "$file" || { printf 'CHYBA: chýba súbor %s\n' "$file" >&2; exit 1; }
  cp -p -- "$file" "$BACKUP_DIR/$(basename "$file")"
done

# Opraví iba testovacie factory bloky, ktoré boli omylom zmenené z dict(...) na
# neplatné data = { key=value }. Zároveň opraví data.update(key=value, ...)
# na platný data.update({"key": value, ...}). Ostatný obsah súborov necháva tak.
python3 - "${FILES[@]}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path


def convert_keyword_lines(body: str) -> str:
    # Konvertuje iba začiatok riadku s identifikátorom; vnorené výrazy ostanú nedotknuté.
    return re.sub(
        r"^(\s*)([A-Za-z_]\w*)=",
        r'\1"\2": ',
        body,
        flags=re.MULTILINE,
    )


def fix_file(name: str) -> None:
    path = Path(name)
    text = path.read_text(encoding="utf-8")
    original = text

    # 1) data = dict(...) -> data = {...}; zároveň prevedie keyword argumenty na dict položky.
    dict_pattern = re.compile(
        r"(?ms)^(?P<indent>\s*)data\s*=\s*dict\(\n(?P<body>.*?)(?P=indent)\)\n(?P<update>\s*data\.update\(overrides\))"
    )

    def dict_repl(match: re.Match[str]) -> str:
        indent = match.group("indent")
        body = convert_keyword_lines(match.group("body"))
        return f"{indent}data = {{\n{body}{indent}}}\n{match.group('update')}"

    text, dict_count = dict_pattern.subn(dict_repl, text, count=1)

    # 2) Ak už je otvorenie data = {, opraví len keyword položky v prvom takom bloku.
    if dict_count == 0:
        brace_pattern = re.compile(
            r"(?ms)^(?P<indent>\s*)data\s*=\s*\{\n(?P<body>.*?)(?P=indent)\}\n(?P<update>\s*data\.update\(overrides\))"
        )

        def brace_repl(match: re.Match[str]) -> str:
            body = convert_keyword_lines(match.group("body"))
            return f"{match.group('indent')}data = {{\n{body}{match.group('indent')}}}\n{match.group('update')}"

        text, _ = brace_pattern.subn(brace_repl, text, count=1)

    # 3) Opraví keyword štýl v data.update(...), ak sa v súbore ešte nachádza.
    update_pattern = re.compile(
        r"(?ms)^(?P<indent>\s*)data\.update\(\n(?P<body>.*?)(?P=indent)\)"
    )

    def update_repl(match: re.Match[str]) -> str:
        body = match.group("body")
        if not re.search(r"^\s*[A-Za-z_]\w*=", body, flags=re.MULTILINE):
            return match.group(0)
        converted = convert_keyword_lines(body)
        return f"{match.group('indent')}data.update({{\n{converted}{match.group('indent')}}})"

    text, _ = update_pattern.subn(update_repl, text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"upravené: {path}")
    else:
        print(f"bez zmeny: {path} (pravdepodobne už opravené)")


for filename in sys.argv[1:]:
    fix_file(filename)
PY

# Doplní package marker iba v prípade, že chýba; nemení existujúci obsah.
if [ ! -e tests/__init__.py ]; then
  : > tests/__init__.py
  printf 'doplnené: tests/__init__.py\n'
fi

# Najprv syntax, potom formatter/linter iba nad dotknutými testami.
python3 -m py_compile "${FILES[@]}"

if command -v ruff >/dev/null 2>&1; then
  ruff format "${FILES[@]}"
  ruff check --fix "${FILES[@]}"
else
  printf 'INFO: ruff nie je dostupný; preskakujem ruff format/check.\n'
fi

python3 -m py_compile "${FILES[@]}"
pytest "${FILES[@]}" -q --no-cov

git diff --check
git status -sb
printf '\nOK: opravy prebehli; záloha je v %s\n' "$BACKUP_DIR"
printf 'Ďalší krok: skontroluj git diff a až potom prípadne git add/commit/push ručne.\n'
