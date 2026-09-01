#!/data/data/com.termux/files/usr/bin/bash
set -eu

cd "$HOME/waste-platform"

echo '===== TIME ====='
date -u '+%Y-%m-%dT%H:%M:%SZ'
echo

echo '===== MAIN SYNTAX CHECK ====='
python -m py_compile "$HOME/waste-platform/app/main.py"
echo "MAIN_PY_COMPILE_OK"
echo

echo '===== HANDLERS SYNTAX CHECK ====='
python -m py_compile "$HOME/waste-platform/app/core/http_exception_handlers.py"
echo "HANDLERS_PY_COMPILE_OK"
echo

echo '===== IMPORT APP.MAIN ====='
python - <<'PY'
import app.main
print("IMPORT_APP_MAIN_OK")
print("APP_OBJECT_TYPE=", type(app.main.app).__name__)
print("MOUNTED_ROUTERS=", getattr(app.main.app.state, "mounted_routers", None))
PY
echo

echo '===== START UVICORN FOREGROUND ====='
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
