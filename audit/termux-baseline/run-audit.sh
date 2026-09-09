#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/audit/termux-baseline"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$OUT/report-$STAMP.txt"

mkdir -p "$OUT"

{
  echo "WASTE-PLATFORM: TERMUX BASELINE AUDIT"
  echo "Generated: $(date -Is)"
  echo "Root: $ROOT"
  echo

  echo "== Git stav =="
  git -C "$ROOT" status --short --branch 2>&1 || true
  echo

  echo "== Aktuálna vetva a posledný commit =="
  git -C "$ROOT" log -1 --oneline 2>&1 || true
  echo

  echo "== Zdrojové adresáre =="
  find "$ROOT" -maxdepth 2 -type d \
    ! -path "$ROOT/.git*" \
    ! -path "$ROOT/.venv*" \
    ! -path "$ROOT/node_modules*" \
    ! -path "$ROOT/audit*" \
    -printf '%p
' 2>/dev/null | sort
  echo

  echo "== Python syntax: zdrojové súbory =="
  PY_COUNT=0
  PY_FAIL=0
  while IFS= read -r -d '' file; do
    PY_COUNT=$((PY_COUNT + 1))
    if ! python -m py_compile "$file" 2>&1; then
      PY_FAIL=$((PY_FAIL + 1))
      echo "FAIL: $file"
    fi
  done < <(
    find "$ROOT/src" "$ROOT/tests" "$ROOT/apps" \
      -type f -name '*.py' -print0 2>/dev/null
  )
  echo "Python files checked: $PY_COUNT"
  echo "Python syntax failures: $PY_FAIL"
  echo

  echo "== ShellCheck: shell skripty =="
  if command -v shellcheck >/dev/null 2>&1; then
    while IFS= read -r -d '' file; do
      echo "--- $file ---"
      shellcheck -x -S warning "$file" 2>&1 || true
    done < <(
      find "$ROOT" -type f -name '*.sh' \
        ! -path "$ROOT/.git/*" \
        ! -path "$ROOT/.venv/*" \
        ! -path "$ROOT/node_modules/*" \
        ! -path "$ROOT/audit/*" \
        -print0 2>/dev/null
    )
  else
    echo "SKIP: shellcheck nie je nainštalovaný."
  fi
  echo

  echo "== YAML kontrola =="
  if command -v yamllint >/dev/null 2>&1; then
    find "$ROOT" -type f ( -name '*.yml' -o -name '*.yaml' ) \
      ! -path "$ROOT/.git/*" \
      ! -path "$ROOT/.venv/*" \
      ! -path "$ROOT/node_modules/*" \
      ! -path "$ROOT/audit/*" \
      -print0 2>/dev/null \
      | xargs -0 -r yamllint -f parsable 2>&1 || true
  else
    echo "SKIP: yamllint nie je nainštalovaný."
  fi
  echo

  echo "== GitHub Actions kontrola =="
  if command -v actionlint >/dev/null 2>&1 && [ -d "$ROOT/.github/workflows" ]; then
    actionlint "$ROOT"/.github/workflows/*.{yml,yaml} 2>&1 || true
  else
    echo "SKIP: actionlint alebo .github/workflows nie je dostupný."
  fi
  echo

  echo "== Dockerfile kontrola =="
  if command -v hadolint >/dev/null 2>&1; then
    find "$ROOT" -type f ( -iname 'Dockerfile' -o -iname 'Dockerfile.*' ) \
      ! -path "$ROOT/.git/*" \
      ! -path "$ROOT/.venv/*" \
      ! -path "$ROOT/node_modules/*" \
      -print0 2>/dev/null \
      | while IFS= read -r -d '' file; do
          echo "--- $file ---"
          hadolint "$file" 2>&1 || true
        done
  else
    echo "SKIP: hadolint nie je nainštalovaný."
  fi
  echo

  echo "== JSON syntax: projektové JSON súbory =="
  JSON_COUNT=0
  JSON_FAIL=0
  while IFS= read -r -d '' file; do
    JSON_COUNT=$((JSON_COUNT + 1))
    if ! python -m json.tool "$file" >/dev/null 2>&1; then
      JSON_FAIL=$((JSON_FAIL + 1))
      echo "FAIL: $file"
    fi
  done < <(
    find "$ROOT" -type f -name '*.json' \
      ! -path "$ROOT/.git/*" \
      ! -path "$ROOT/.venv/*" \
      ! -path "$ROOT/node_modules/*" \
      ! -path "$ROOT/audit/*" \
      -print0 2>/dev/null
  )
  echo "JSON files checked: $JSON_COUNT"
  echo "JSON syntax failures: $JSON_FAIL"
  echo

  echo "== NPM skripty iba na čítanie =="
  while IFS= read -r -d '' package_json; do
    echo "--- $package_json ---"
    python - "$package_json" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
try:
    data = json.loads(p.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    print("name:", data.get("name", "(bez mena)"))
    if scripts:
        for name, command in scripts.items():
            print(f"script {name}: {command}")
    else:
        print("scripts: none")
except Exception as exc:
    print("FAIL:", type(exc).__name__, exc)
PY
  done < <(
    find "$ROOT/apps" -type f -name package.json \
      ! -path "*/node_modules/*" \
      -print0 2>/dev/null
  )
  echo

  echo "== Podozrivé stopy bez čítania .env a dumpov =="
  rg -n --hidden \
    --glob '!.git/**' \
    --glob '!**/.venv/**' \
    --glob '!**/node_modules/**' \
    --glob '!audit/**' \
    --glob '!reports/**' \
    --glob '!audit-output/**' \
    --glob '!backups/**' \
    --glob '!archived/**' \
    --glob '!_quarantine/**' \
    --glob '!.env*' \
    --glob '!dump.rdb' \
    '(TODO|FIXME|NotImplementedError|pass[[:space:]]*$|raise NotImplemented|console.log|debugger;)' \
    "$ROOT/src" "$ROOT/apps" "$ROOT/tests" 2>/dev/null | head -500 || true
  echo

  echo "== Záver =="
  echo "Tento audit nič nemení: nespúšťa Docker, migrácie, npm skripty, testy ani deployment."
  echo "Skontroluj najmä riadky FAIL, warning, error, TODO a FIXME."
} > "$REPORT" 2>&1

ln -sfn "$(basename "$REPORT")" "$OUT/latest.txt"
echo "REPORT=$REPORT"
