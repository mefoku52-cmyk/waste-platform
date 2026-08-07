#!/usr/bin/env bash
set -Eeuo pipefail
cd ~/waste-platform

echo "########################################"
echo "# 1. GIT HISTORIA (existuje vobec?)"
echo "########################################"
git log --oneline --all 2>&1 | head -30
echo "--- Pocet commitov ---"
git rev-list --all --count 2>&1

echo ""
echo "########################################"
echo "# 2. CASOVE PECIATKY: app/ vs backend/"
echo "########################################"
echo "--- Najnovsi zmeneny subor v app/ ---"
find app -name "*.py" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -3
echo "--- Najnovsi zmeneny subor v backend/app ---"
find backend/app -name "*.py" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -3
echo "--- Najstarsi subor v app/ ---"
find app -name "*.py" -printf '%T@ %p\n' 2>/dev/null | sort -n | head -3
echo "--- Najstarsi subor v backend/app ---"
find backend/app -name "*.py" -printf '%T@ %p\n' 2>/dev/null | sort -n | head -3

echo ""
echo "########################################"
echo "# 3. MA backend/ VLASTNY requirements/pyproject?"
echo "########################################"
find backend -maxdepth 1 -iname "requirements*.txt" -o -maxdepth 1 -iname "pyproject.toml" 2>&1
find backend -maxdepth 1 -iname "Dockerfile*" 2>&1

echo ""
echo "########################################"
echo "# 4. Prekryv modulov: co ma backend/, co app/ nema"
echo "########################################"
echo "--- app/modules/* ---"
ls app/modules/ 2>&1
echo "--- backend/app/* (top-level, DDD-styl nie modules/) ---"
ls backend/app/ 2>&1
echo "--- Ma backend nieco z chybajucich 7 modulov (listings/inquiries/documents/compliance/notifications/analytics/admin)? ---"
for m in listings inquiries documents compliance notifications analytics admin; do
  echo -n "  ${m}: "
  grep -rli "$m" backend/app --include="*.py" 2>/dev/null | wc -l
  echo "   subory najdene:"
  grep -rli "$m" backend/app --include="*.py" 2>/dev/null | head -5
done

echo ""
echo "########################################"
echo "# 5. main.py v backend/ - je funkcny vstupny bod?"
echo "########################################"
find backend -iname "main.py" 2>&1
if [ -f backend/app/main.py ]; then
  echo "--- Obsah backend/app/main.py (prvych 30 riadkov) ---"
  head -30 backend/app/main.py
fi

echo ""
echo "########################################"
echo "# 6. DOKONCENIE KROK 12/13: pip install + import test (app/)"
echo "########################################"
rm -rf scripts/grok-audit/test-venv
python3 -m venv scripts/grok-audit/test-venv
set +e
source scripts/grok-audit/test-venv/bin/activate
pip install --quiet --upgrade pip 2>&1 | tail -5
pip install --quiet -r app/requirements.txt 2>&1 | tail -30
PIP_EXIT=$?
echo "PIP INSTALL EXIT CODE: ${PIP_EXIT}"

echo "--- Import test ---"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.shared.presentation.metrics_router import router
    print('METRICS_ROUTER IMPORT OK:', router)
except Exception as e:
    print('METRICS_ROUTER IMPORT ZLYHAL:', repr(e))
try:
    from app.main import app as fastapi_app
    print('MAIN.PY APP IMPORT OK')
except Exception as e:
    print('MAIN.PY APP IMPORT ZLYHAL:', repr(e))
"
deactivate
set -e

echo ""
echo "########################################"
echo "# DIAGNOSTIKA DOKONCENA"
echo "########################################"
