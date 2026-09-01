#!/data/data/com.termux/files/usr/bin/bash
set -eu

MAIN_FILE="$HOME/waste-platform/app/main.py"
STAMP="$(date +%Y%m%d-%H%M%S)"

cp "$MAIN_FILE" "$HOME/waste-platform/app/main.py.bak.fix-handler-placement.$STAMP"

python - <<'PY'
from pathlib import Path

path = Path("/data/data/com.termux/files/home/waste-platform/app/main.py")
text = path.read_text()

bad_line = "register_http_exception_handlers(app)
"
text = text.replace(bad_line, "")

needle = "    )

    app.add_middleware("
replacement = "    )
    register_http_exception_handlers(app)

    app.add_middleware("

if needle not in text:
    raise SystemExit("Could not find FastAPI constructor closing block in app/main.py")

text = text.replace(needle, replacement, 1)

path.write_text(text)
PY

echo '===== PATCHED MAIN.PY ====='
nl -ba "$MAIN_FILE" | sed -n '1,220p'
echo

echo '===== PYTHON SYNTAX CHECK ====='
python -m py_compile "$MAIN_FILE"
echo "PY_COMPILE_OK"
echo

echo '===== RESTART CLEAN BACKEND ====='
pkill -f 'uvicorn app.main:app --host 0.0.0.0 --port 8010' 2>/dev/null || true
sleep 2
nohup "$HOME/waste-platform/run-clean-backend.sh" >/dev/null 2>&1 &
sleep 4
tail -n 120 "$HOME/cmep-backend-clean.log" || true
echo

echo '===== VERIFY LOGIN NOW RETURNS 401 ====='
curl -i -m 10 -X POST http://localhost:8010/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"nonexistent@example.com","password":"wrongpass"}' || true
echo

echo '===== HEALTH ====='
curl -i -m 10 http://localhost:8010/health || true
echo

echo '===== FINAL LOG TAIL ====='
tail -n 120 "$HOME/cmep-backend-clean.log" || true
