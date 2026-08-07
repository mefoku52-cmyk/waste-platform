#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=== BACKEND ISOLATED TEST ==="

rm -rf backend_test_env

python3 -m venv backend_test_env

source backend_test_env/bin/activate

pip install --upgrade pip

pip install -r backend/requirements.txt

cd backend

python3 - <<'PY'
import sys
sys.path.insert(0,'.')

from app.main import app

print("FASTAPI IMPORT OK")
print("ROUTES:", len(app.routes))
PY

echo "=== BACKEND OK ==="
