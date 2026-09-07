#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/map_runtime_wiring_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== MAP RUNTIME WIRING ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cd "$PROJECT"

echo "=== 1. ENTRYPOINT SUBORY ==="
for f in \
  "$PROJECT/app/main.py" \
  "$PROJECT/app/Dockerfile" \
  "$PROJECT/docker-compose.yml" \
  "$PROJECT/docker-compose.monitoring.yml" \
  "$PROJECT/Makefile" \
  "$PROJECT/start-platform.sh" \
  "$PROJECT/pyproject.toml" \
  "$PROJECT/requirements.txt"
do
  if [ -f "$f" ]; then
    echo "[EXISTUJE] $f"
  else
    echo "[CHYBA]    $f"
  fi
done
echo

echo "=== 2. APP MAIN ==="
if [ -f "$PROJECT/app/main.py" ]; then
  nl -ba "$PROJECT/app/main.py" | sed -n '1,240p'
else
  echo "[CHYBA] app/main.py neexistuje"
fi
echo

echo "=== 3. FASTAPI WIRING ==="
grep -RniE 'FastAPI\(|include_router\(|APIRouter\(|@router\.get|@router\.post|@router\.put|@router\.delete' \
  "$PROJECT/app" --include='*.py' 2>/dev/null || true
echo

echo "=== 4. ROUTER SUBORY ==="
find "$PROJECT/app" -type f \( -name 'router.py' -o -name '*_router.py' -o -path '*/presentation/*.py' \) \
  | sed "s|$PROJECT|.|" | sort
echo

echo "=== 5. COMPOSE SLUZBY A BUILD CESTY ==="
for f in "$PROJECT/docker-compose.yml" "$PROJECT/docker-compose.monitoring.yml"; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    grep -nE 'services:|image:|build:|context:|dockerfile:|ports:|env_file:|depends_on:|volumes:' "$f" || true
    echo
  fi
done

echo "=== 6. APPS/ STROM ==="
if [ -d "$PROJECT/apps" ]; then
  find "$PROJECT/apps" -maxdepth 3 \
    \( -path '*/.next' -o -path '*/node_modules' -o -path '*/dist' -o -path '*/build' \) -prune \
    -o -print | sed "s|$PROJECT|.|" | sort
else
  echo "[INFO] apps/ neexistuje"
fi
echo

echo "=== 7. TESTY ==="
for d in "$PROJECT/tests" "$PROJECT/app/tests"; do
  if [ -d "$d" ]; then
    echo "--- $d ---"
    find "$d" -type f | sed "s|$PROJECT|.|" | sort
  fi
done
echo

echo "=== 8. KORENOVE SHELL SKRIPTY ==="
find "$PROJECT" -maxdepth 1 -type f -name '*.sh' | sed "s|$PROJECT|.|" | sort
echo

echo "=== 9. KORENOVE TXT ARTEFAKTY ==="
find "$PROJECT" -maxdepth 1 -type f -name '*.txt' | sed "s|$PROJECT|.|" | sort
echo

echo "=== 10. 0-BAJTOVE MARKERY V KORENI ==="
find "$PROJECT" -maxdepth 1 -type f -size 0c | sed "s|$PROJECT|.|" | sort
echo

echo "=== 11. STRUCNY FAKTICKY ZAVER ==="
echo "[A] Co je pravdepodobne runtime jadro: app/, compose, Dockerfile, start skripty"
echo "[B] Co je pravdepodobne frontend alebo doplnok: apps/"
echo "[C] Co su testy: tests/, app/tests/"
echo "[D] Co su auditne alebo historicke artefakty: root *.txt a cast root *.sh"
echo "[E] Co treba overit dalsim krokom: ktore root skripty sa realne pouzivaju"
echo
echo "REPORT: $REPORT"
echo "=== KONIEC MAP RUNTIME WIRING ==="
