#!/usr/bin/env bash
set -Eeuo pipefail
cd ~/waste-platform

echo "########################################"
echo "# 1. api_router.py — riesi otazku auth na /metrics"
echo "########################################"
if [ -f app/shared/presentation/api_router.py ]; then
  cat app/shared/presentation/api_router.py
else
  echo "[CHYBA] subor neexistuje"
fi

echo ""
echo "########################################"
echo "# 2. exception_handlers.py — mapovanie UnauthorizedDomainError"
echo "########################################"
if [ -f app/shared/presentation/exception_handlers.py ]; then
  cat app/shared/presentation/exception_handlers.py
else
  echo "[CHYBA] subor neexistuje"
fi

echo ""
echo "########################################"
echo "# 3. UnauthorizedDomainError definicia"
echo "########################################"
grep -n "UnauthorizedDomainError" app/shared/domain/exceptions.py 2>&1

echo ""
echo "########################################"
echo "# 4. DOKONCENIE pip install + import test (bez skratenia)"
echo "########################################"
rm -rf scripts/grok-audit/test-venv
python3 -m venv scripts/grok-audit/test-venv
set +e
source scripts/grok-audit/test-venv/bin/activate
echo "--- pip upgrade ---"
pip install --upgrade pip 2>&1
echo "--- pip install requirements ---"
pip install -r app/requirements.txt 2>&1
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
    routes = [r.path for r in fastapi_app.routes]
    print('ZAREGISTROVANE ROUTES:', routes)
except Exception as e:
    print('MAIN.PY APP IMPORT ZLYHAL:', repr(e))
"
deactivate
set -e

echo ""
echo "########################################"
echo "# 5. Obsah 3 novo-existujucich modulov (kostry vs realna logika)"
echo "########################################"
for m in listings documents admin; do
  echo "--- ${m}: pocet riadkov v kazdom .py subore ---"
  find app/modules/${m} -name "*.py" -not -path "*__pycache__*" | xargs wc -l | sort -n
done

echo ""
echo "########################################"
echo "# DIAGNOSTIKA 2 DOKONCENA"
echo "########################################"
