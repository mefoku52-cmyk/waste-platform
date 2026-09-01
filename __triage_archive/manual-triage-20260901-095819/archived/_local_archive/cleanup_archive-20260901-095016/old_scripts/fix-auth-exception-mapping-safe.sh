#!/data/data/com.termux/files/usr/bin/bash
set -eu

MAIN_FILE="$HOME/waste-platform/app/main.py"
HANDLERS_FILE="$HOME/waste-platform/app/core/http_exception_handlers.py"
STAMP="$(date +%Y%m%d-%H%M%S)"

cp "$MAIN_FILE" "$HOME/waste-platform/app/main.py.bak.$STAMP"

cat > "$HANDLERS_FILE" <<'PYEOF'
from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.domain.exceptions import (
    NotFoundDomainError,
    UnauthorizedDomainError,
    ValidationDomainError,
)


def register_http_exception_handlers(app):
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
PYEOF

if ! grep -q 'from app.core.http_exception_handlers import register_http_exception_handlers' "$MAIN_FILE"; then
  sed -i '/from app.core.config import settings/a from app.core.http_exception_handlers import register_http_exception_handlers' "$MAIN_FILE"
fi

if ! grep -q 'register_http_exception_handlers(app)' "$MAIN_FILE"; then
  sed -i '/app = FastAPI/a register_http_exception_handlers(app)' "$MAIN_FILE"
fi

echo '===== HANDLERS FILE ====='
nl -ba "$HANDLERS_FILE" | sed -n '1,220p'
echo

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
