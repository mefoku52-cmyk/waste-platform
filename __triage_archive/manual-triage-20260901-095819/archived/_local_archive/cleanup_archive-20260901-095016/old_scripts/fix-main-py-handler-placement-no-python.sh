#!/data/data/com.termux/files/usr/bin/bash
set -eu

MAIN_FILE="$HOME/waste-platform/app/main.py"
TMP_FILE="$HOME/waste-platform/app/main.py.tmp"
STAMP="$(date +%Y%m%d-%H%M%S)"

cp "$MAIN_FILE" "$HOME/waste-platform/app/main.py.bak.fix-handler-placement.$STAMP"

sed '/^[[:space:]]*register_http_exception_handlers(app)[[:space:]]*$/d' "$MAIN_FILE" > "$TMP_FILE"

awk '
BEGIN { inserted=0 }
{
  print
  if (inserted==0 && $0 ~ /^    )$/) {
    print "    register_http_exception_handlers(app)"
    inserted=1
  }
}
END {
  if (inserted==0) {
    exit 7
  }
}
' "$TMP_FILE" > "$MAIN_FILE"

rm -f "$TMP_FILE"

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
