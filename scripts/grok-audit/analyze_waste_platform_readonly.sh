#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/analyze_waste_platform_report.txt"

mkdir -p "$OUTDIR"

exec > >(tee "$REPORT") 2>&1

echo "=== ANALYZA WASTE-PLATFORM / READ-ONLY ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

if [ ! -d "$PROJECT" ]; then
  echo "[CHYBA] Projektovy adresar neexistuje: $PROJECT"
  exit 1
fi

cd "$PROJECT"

echo "=== 1. IDENTITA A KOREN PROJEKTU ==="
pwd
echo
echo "--- KORENOVE POLOZKY ---"
ls -la
echo

echo "=== 2. ADRESAROVA STRUKTURA DO HLBKY 3 ==="
find "$PROJECT" -maxdepth 3 \
  \( -path '*/.git' -o -path '*/node_modules' -o -path '*/__pycache__' -o -path '*/.next' -o -path '*/dist' -o -path '*/build' \) -prune \
  -o -print | sed "s|$PROJECT|.|" | sort
echo

echo "=== 3. KLUCOVE SUBORY A ICH EXISTENCIA ==="
for f in \
  "$PROJECT/README.md" \
  "$PROJECT/docker-compose.yml" \
  "$PROJECT/docker-compose.monitoring.yml" \
  "$PROJECT/pyproject.toml" \
  "$PROJECT/requirements.txt" \
  "$PROJECT/.env" \
  "$PROJECT/.env.example" \
  "$PROJECT/.env.production" \
  "$PROJECT/app/Dockerfile" \
  "$PROJECT/app/requirements.txt" \
  "$PROJECT/app/main.py"
do
  if [ -e "$f" ]; then
    echo "[EXISTUJE] $f"
  else
    echo "[CHYBA]    $f"
  fi
done
echo

echo "=== 4. README A DOKUMENTACNE SIGNALY ==="
if [ -f "$PROJECT/README.md" ]; then
  echo "--- README prvych 200 riadkov ---"
  nl -ba "$PROJECT/README.md" | sed -n '1,200p'
else
  echo "[INFO] README.md neexistuje"
fi
echo
echo "--- DOCS STROM ---"
if [ -d "$PROJECT/docs" ]; then
  find "$PROJECT/docs" -maxdepth 3 -type f | sed "s|$PROJECT|.|" | sort
else
  echo "[INFO] docs/ neexistuje"
fi
echo

echo "=== 5. APP STRUKTURA A PYTHON SUBORY ==="
if [ -d "$PROJECT/app" ]; then
  find "$PROJECT/app" -type f \( -name '*.py' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.toml' \) \
    | sed "s|$PROJECT|.|" | sort
else
  echo "[INFO] app/ neexistuje"
fi
echo

echo "=== 6. PYTHON IMPORTY A SYNTAX ==="
cat > "$OUTDIR/_extract_imports_full.py" <<'PYEOF'
import ast
import pathlib
import sys

root = pathlib.Path("app")
stdlib = set(getattr(sys, "stdlib_module_names", []))
all_imports = {}
syntax_errors = []

if root.exists():
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError as e:
            syntax_errors.append(f"{py_file}: {e}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    imports.add(node.module.split(".")[0])
        all_imports[str(py_file)] = sorted(imports)

print("=== IMPORTY PODLA SUBOROV ===")
for path in sorted(all_imports):
    print(f"[SUBOR] {path}")
    for mod in all_imports[path]:
        print(f"  - {mod}")

external = sorted({
    mod
    for mods in all_imports.values()
    for mod in mods
    if mod not in stdlib and mod != "app"
})
print("\n=== EXTERNE IMPORTY UNIKATNE ===")
for mod in external:
    print(mod)

print("\n=== SYNTAX CHYBY ===")
if syntax_errors:
    for err in syntax_errors:
        print(err)
else:
    print("ZIADNE")
PYEOF

python3 "$OUTDIR/_extract_imports_full.py"
echo

echo "=== 7. PY_COMPILE KONTROLA VSETKYCH .PY ==="
find "$PROJECT/app" -type f -name '*.py' | sort | while read -r f; do
  if python3 -m py_compile "$f" 2>/dev/null; then
    echo "[SYNTAX OK] $f"
  else
    echo "[SYNTAX ERROR] $f"
    python3 -m py_compile "$f" 2>&1 || true
  fi
done
echo

echo "=== 8. DOCKER A COMPOSE SIGNALY ==="
for f in "$PROJECT/docker-compose.yml" "$PROJECT/docker-compose.monitoring.yml" "$PROJECT/app/Dockerfile"; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    nl -ba "$f"
    echo
  fi
done

echo "--- GREP SIGNALY: build/context/dockerfile/image/ports/env_file/volumes/depends_on ---"
grep -RniE 'build:|context:|dockerfile:|image:|ports:|env_file:|volumes:|depends_on:' \
  "$PROJECT/docker-compose.yml" "$PROJECT/docker-compose.monitoring.yml" "$PROJECT/app/Dockerfile" 2>/dev/null || true
echo

echo "=== 9. ENV SIGNALY BEZ UNIKU HODNOT ==="
for f in "$PROJECT/.env" "$PROJECT/.env.example" "$PROJECT/.env.production"; do
  if [ -f "$f" ]; then
    echo "--- PREMENNE V $f ---"
    sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1=/p' "$f" | sort
  else
    echo "[INFO] NEEXISTUJE $f"
  fi
  echo
done

echo "=== 10. FASTAPI/WIRING SIGNALY ==="
grep -RniE 'FastAPI\(|APIRouter\(|include_router\(|@router\.|@app\.' "$PROJECT/app" --include='*.py' 2>/dev/null || true
echo

echo "=== 11. AUTH/SECURITY SIGNALY ==="
grep -RniE 'jwt|JWT|passlib|CryptContext|OAuth2|Depends\(|Authorization|Bearer|SECRET|CORS|CORSMiddleware' \
  "$PROJECT/app" "$PROJECT/infra" "$PROJECT/docs" --include='*.py' --include='*.yml' --include='*.yaml' --include='*.md' 2>/dev/null || true
echo

echo "=== 12. TESTY ==="
if [ -d "$PROJECT/tests" ]; then
  find "$PROJECT/tests" -type f | sed "s|$PROJECT|.|" | sort
else
  echo "[INFO] tests/ neexistuje"
fi
if [ -d "$PROJECT/app/tests" ]; then
  find "$PROJECT/app/tests" -type f | sed "s|$PROJECT|.|" | sort
fi
echo

echo "=== 13. SHELL SKRIPTY A PODOZRIVE ARTEFAKTY ==="
find "$PROJECT" -type f \
  \( -name '*.sh' -o -name '*.bak' -o -name '*.tmp' -o -name '*.old' -o -name '*~' \) \
  | sed "s|$PROJECT|.|" | sort
echo

echo "=== 14. PLACEHOLDER A TODO SIGNALY ==="
grep -RniE 'TODO|FIXME|XXX|placeholder|stub|mock|dummy|pass$|NotImplementedError|raise HTTPException|return None' \
  "$PROJECT/app" "$PROJECT/apps" "$PROJECT/docs" "$PROJECT/tests" --include='*.py' --include='*.md' --include='*.tsx' --include='*.ts' --include='*.js' --include='*.jsx' 2>/dev/null || true
echo

echo "=== 15. ARCHITEKTURNE SIGNALY PODLA NAZVOV ==="
find "$PROJECT/app" -type f | sed "s|$PROJECT|.|" | grep -Ei 'domain|application|infrastructure|presentation|router|service|repository|schema|model|entity|use_case|usecase' || true
echo

echo "=== 16. KRATKY STROJOVY ZAVER Z DOKAZOV ==="
echo "[A] Co projekt chce byt: odhadni iba zo suborov README, docs, compose, app/main.py"
echo "[B] Co uz existuje: vypis len potvrdene moduly a subory"
echo "[C] Co je navyse alebo podozrive: bak/tmp/duplicitne skripty/prazdne znacnikove subory"
echo "[D] Co treba opravit: syntax chyby, chybajuce subory, wiring, manifesty"
echo "[E] Co sa neda rozhodnut: explicitne vypis ako NEISTOTA"
echo
echo "=== KONIEC ANALYZY ==="
echo "REPORT: $REPORT"
