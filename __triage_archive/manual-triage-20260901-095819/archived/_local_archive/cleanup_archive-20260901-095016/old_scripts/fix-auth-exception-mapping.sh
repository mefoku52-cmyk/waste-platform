#!/data/data/com.termux/files/usr/bin/bash
set -eu

MAIN_FILE="$HOME/waste-platform/app/main.py"
BACKUP_FILE="$HOME/waste-platform/app/main.py.bak.$(date +%Y%m%d-%H%M%S)"

cp "$MAIN_FILE" "$BACKUP_FILE"

python - <<'PY'
from pathlib import Path
import re

path = Path("/data/data/com.termux/files/home/waste-platform/app/main.py")
text = path.read_text()

if "from fastapi import FastAPI, Request" not in text:
    text = text.replace(
        "from fastapi import FastAPI",
        "from fastapi import FastAPI, Request",
    )

if "from fastapi.responses import JSONResponse" not in text:
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from fastapi import "):
            insert_at = i + 1
            break
    lines.insert(insert_at, "from fastapi.responses import JSONResponse")
    text = "
".join(lines) + "
"

if "from app.shared.domain.exceptions import" not in text:
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from app.core.config import settings"):
            insert_at = i + 1
            break
    lines.insert(
        insert_at,
        "from app.shared.domain.exceptions import UnauthorizedDomainError, NotFoundDomainError, ValidationDomainError",
    )
    text = "
".join(lines) + "
"

if "@app.exception_handler(UnauthorizedDomainError)" not in text:
    handler_block = '''

@app.exception_handler(UnauthorizedDomainError)
async def unauthorized_domain_handler(request: Request, exc: UnauthorizedDomainError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc) or "Unauthorized"},
    )

@app.exception_handler(NotFoundDomainError)
async def not_found_domain_handler(request: Request, exc: NotFoundDomainError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Not found"},
    )

@app.exception_handler(ValidationDomainError)
async def validation_domain_handler(request: Request, exc: ValidationDomainError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc) or "Validation error"},
    )
'''

    match = re.search(r'(?m)^@app.(get|post|put|patch|delete)(', text)
    if not match:
        raise SystemExit("Could not find first FastAPI route decorator in app/main.py")

    text = text[:match.start()] + handler_block + "

" + text[match.start():]

path.write_text(text)
PY

echo '===== PATCHED MAIN.PY ====='
nl -ba "$MAIN_FILE" | sed -n '1,220p'
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
