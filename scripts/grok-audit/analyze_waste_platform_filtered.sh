#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/analyze_waste_platform_filtered_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== FILTERED ANALYZA WASTE-PLATFORM ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

if [ ! -d "$PROJECT" ]; then
  echo "[CHYBA] Projekt neexistuje: $PROJECT"
  exit 1
fi

cd "$PROJECT"

echo "=== 1. ROOT PREHLAD ==="
ls -la
echo

echo "=== 2. RUNTIME CODE FILES ==="
find "$PROJECT/app" "$PROJECT/apps" "$PROJECT/tests" \
  \( -path '*/__pycache__/*' -o -path '*/.next/*' -o -path '*/node_modules/*' -o -path '*/dist/*' -o -path '*/build/*' \) -prune \
  -o -type f \
  \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.toml' \) \
  -print 2>/dev/null | sed "s|$PROJECT|.|" | sort
echo

echo "=== 3. DOCS ONLY ==="
if [ -d "$PROJECT/docs" ]; then
  find "$PROJECT/docs" -type f | sed "s|$PROJECT|.|" | sort
else
  echo "[INFO] docs/ neexistuje"
fi
echo

echo "=== 4. GENERATED OR CACHE ==="
find "$PROJECT" \
  \( -path '*/__pycache__/*' -o -path '*/.next/*' -o -path '*/node_modules/*' -o -path '*/dist/*' -o -path '*/build/*' \) \
  -print 2>/dev/null | sed "s|$PROJECT|.|" | sort | head -n 400
echo

echo "=== 5. SUSPICIOUS OR EXTRA FILES ==="
find "$PROJECT" -type f \
  \( -name '*.bak' -o -name '*.old' -o -name '*.tmp' -o -name '*.unused*' -o -name '*~' \) \
  -print 2>/dev/null | sed "s|$PROJECT|.|" | sort
echo

echo "=== 6. ROOT MARKER FILES (0-BYTE / STATUS FILES) ==="
find "$PROJECT" -maxdepth 1 -type f -size 0c -print | sed "s|$PROJECT|.|" | sort
echo

echo "=== 7. TODO / FIXME LEN V RUNTIME KODE ==="
grep -RniE 'TODO|FIXME|XXX|NotImplementedError|pass$|return None|placeholder|stub|mock|dummy' \
  "$PROJECT/app" "$PROJECT/apps" "$PROJECT/tests" \
  --include='*.py' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' 2>/dev/null || true
echo

echo "=== 8. TODO / FIXME LEN V DOCS ==="
grep -RniE 'TODO|FIXME|XXX|NotImplementedError|pass$|return None|placeholder|stub|mock|dummy' \
  "$PROJECT/docs" \
  --include='*.md' --include='*.txt' 2>/dev/null || true
echo

echo "=== 9. MOZNE DUPLICITY PODLA NAZVU ==="
find "$PROJECT/app" -type f 2>/dev/null | sed 's#.*/##' | sort | uniq -d
echo

echo "=== 10. PODOZRIVE DUPLICITY A REFERENCIE ==="
for f in \
  "$PROJECT/app/shared/infrastructure/database.py" \
  "$PROJECT/app/shared/infrastructure/database.py.unused_duplicate" \
  "$PROJECT/app/shared/infrastructure/rate_limit.py" \
  "$PROJECT/app/shared/infrastructure/rate_limiter.py"
do
  if [ -f "$f" ]; then
    echo "--- EXISTUJE: $f ---"
    grep -Rni -- "$(basename "$f" | sed 's/\./\\./g')" "$PROJECT/app" "$PROJECT/tests" 2>/dev/null || true
    echo
  fi
done

echo "=== 11. MAIN ENTRYPOINTS A WIRING ==="
grep -RniE 'FastAPI\(|include_router\(|APIRouter\(|uvicorn|main:app' \
  "$PROJECT/app" "$PROJECT/apps" "$PROJECT/docker-compose.yml" "$PROJECT/app/Dockerfile" \
  --include='*.py' --include='*.yml' --include='*.yaml' 2>/dev/null || true
echo

echo "=== 12. STRUCNY FAKTICKY SUHRN Z DOKAZOV ==="
echo "[A] Backend runtime strom: potvrdeny len podla app/"
echo "[B] Frontend/build artefakty: oddelene od runtime"
echo "[C] Docs tvrdenia: neplatia automaticky pre runtime"
echo "[D] Extra/podozrive subory: len tie, ktore boli realne najdene"
echo "[E] Neistota: co bez referencii a bez spustenia nejde rozhodnut"
echo
echo "REPORT: $REPORT"
echo "=== KONIEC FILTERED ANALYZY ==="
