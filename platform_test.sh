#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=== WASTE PLATFORM TEST ==="

echo "[1] Python syntax"
python3 -m compileall backend app

echo "[2] Requirements"
python3 -m pip check || true

echo "[3] Structure"

for d in backend app frontend docker scripts docs; do
    if [ -d "$d" ]; then
        echo "OK $d"
    else
        echo "MISSING $d"
    fi
done

echo "[4] FastAPI import"

cd backend

python3 - <<'PY'
import sys
sys.path.insert(0,'.')

try:
    from app.main import app
    print("FASTAPI IMPORT OK")
except Exception as e:
    print("FASTAPI ERROR:")
    print(e)
PY

echo "=== DONE ==="
