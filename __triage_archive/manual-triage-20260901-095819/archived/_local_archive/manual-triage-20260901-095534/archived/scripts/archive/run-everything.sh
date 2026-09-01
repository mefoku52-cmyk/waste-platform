#!/bin/bash
# ==============================================================================
# run-everything.sh — Master script pre CMEP
# Robí: fixy, cleanup, PostgreSQL+Redis startup, smoke test, uvicorn
# Spusti:  bash ~/waste-platform/run-everything.sh
# ==============================================================================
set -euo pipefail

ROOT="$HOME/waste-platform"
BACKUP="$ROOT/.fix-backup-$(date +%Y%m%d-%H%M%S)"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERR]${NC} $1"; }

mkdir -p "$BACKUP"

# ==============================================================================
# 1. FIX .env — lowercase -> uppercase (idempotent)
# ==============================================================================
fix_env() {
    local f="$ROOT/.env"
    [ -f "$f" ] || { warn ".env nenájdený"; return; }
    cp "$f" "$BACKUP/.env" 2>/dev/null || true
    python3 - "$f" << 'PY'
import sys
f = sys.argv[1]
with open(f) as fh: lines = fh.readlines()
mapping = {
    'app_env':'APP_ENV','app_host':'APP_HOST','app_port':'APP_PORT',
    'database_url':'DATABASE_URL','redis_url':'REDIS_URL',
    'jwt_secret_key':'JWT_SECRET_KEY','jwt_refresh_secret_key':'JWT_REFRESH_SECRET_KEY',
    'jwt_access_token_expires_minutes':'JWT_ACCESS_TOKEN_EXPIRES_MINUTES',
    'jwt_refresh_token_expires_days':'JWT_REFRESH_TOKEN_EXPIRES_DAYS',
    'next_public_api_base_url':'NEXT_PUBLIC_API_BASE_URL',
}
out = []
for line in lines:
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        out.append(line); continue
    key = s.split('=',1)[0]
    low = key.lower()
    if low in mapping and key != mapping[low]:
        line = line.replace(key, mapping[low], 1)
    out.append(line)
with open(f,'w') as fh: fh.writelines(out)
PY
    ok ".env: lowercase -> uppercase"
}

# ==============================================================================
# 2. FIX config.py — extra='ignore' (idempotent)
# ==============================================================================
fix_config() {
    local f="$ROOT/app/core/config.py"
    cp "$f" "$BACKUP/config.py" 2>/dev/null || true
    if grep -q 'model_config' "$f" 2>/dev/null; then
        ok "config.py: model_config už existuje"; return
    fi
    python3 - "$f" << 'PY'
import sys, re
f = sys.argv[1]
with open(f) as fh: c = fh.read()
if "SettingsConfigDict" not in c:
    c = c.replace("from pydantic_settings import BaseSettings",
                  "from pydantic_settings import BaseSettings, SettingsConfigDict")
c = re.sub(r'(class Settings\(BaseSettings\):\n)(\s*)',
           r'\1\2model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8")\n\2', c)
with open(f,'w') as fh: fh.write(c)
PY
    ok "config.py: pridaný extra='ignore'"
}

# ==============================================================================
# 3. FIX main.py — modulárny router (idempotent)
# ==============================================================================
fix_main() {
    local f="$ROOT/app/main.py"
    cp "$f" "$BACKUP/main.py" 2>/dev/null || true
    sed -i 's|from app\.api\.v1\.router import api_router|from app.shared.presentation.api_router import api_router|' "$f"
    sed -i 's|from app\.api\.internal import metrics_router|from app.shared.presentation.metrics_router import router as metrics_router|' "$f"
    ok "main.py: modulárny router"
}

# ==============================================================================
# 4. FIX company_memberships prefix (idempotent)
# ==============================================================================
fix_memberships_prefix() {
    local f="$ROOT/app/modules/company_memberships/presentation/router.py"
    if grep -q 'APIRouter()' "$f" 2>/dev/null; then
        sed -i 's|APIRouter()|APIRouter(prefix="/company-memberships", tags=["company-memberships"])|' "$f"
        ok "company_memberships: pridaný prefix /company-memberships"
    else
        ok "company_memberships: prefix už je nastavený"
    fi
}

# ==============================================================================
# 5. ARCHIVÁCIA starého app/api/v1/
# ==============================================================================
archive_old_api() {
    if [ -d "$ROOT/app/api/v1" ]; then
        local a="$ROOT/.archived-api-v1-$(date +%Y%m%d-%H%M%S)"
        cp -a "$ROOT/app/api/v1" "$a/"
        rm -rf "$ROOT/app/api/v1"
        ok "Starý app/api/v1 archivovaný do $a"
    else
        ok "app/api/v1/ neexistuje — preskakujem"
    fi
}

# ==============================================================================
# 6. ZMAZANIE .bak súborov
# ==============================================================================
cleanup_bak() {
    local n=$(find "$ROOT/app/modules" -type f -name "*.bak*" -print -delete 2>/dev/null | wc -l)
    ok "Zmazaných .bak súborov: $n"
}

# ==============================================================================
# 7. POSTGRESQL — robustný startup s PID cleanup
# ==============================================================================
start_postgres() {
    local PGDATA="${PREFIX:-/data/data/com.termux/files/usr}/var/lib/postgresql"
    local PIDFILE="$PGDATA/postmaster.pid"
    
    if pg_isready -q 2>/dev/null; then
        ok "PostgreSQL už beží"; return
    fi
    
    if [ -f "$PIDFILE" ]; then
        local OLD_PID=$(head -n1 "$PIDFILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            ok "PostgreSQL beží (PID $OLD_PID)"; return
        else
            warn "Mŕtvy postmaster.pid (PID $OLD_PID), čistím..."
            rm -f "$PIDFILE"
        fi
    fi
    
    pg_ctl -D "$PGDATA" start -l "$PGDATA/log" 2>/dev/null || {
        err "PostgreSQL sa nepodarilo štartnúť"; return 1
    }
    sleep 2
    if pg_isready -q 2>/dev/null; then
        ok "PostgreSQL štartnutý"
    else
        warn "PostgreSQL ešte nie je ready, skúsim znova o 3 sekundy..."
        sleep 3
        pg_isready -q && ok "PostgreSQL ready" || err "PostgreSQL stále nie je ready"
    fi
}

# ==============================================================================
# 8. REDIS — štart ak nebeží
# ==============================================================================
start_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        ok "Redis už beží"; return
    fi
    redis-server --daemonize yes
    sleep 1
    if redis-cli ping >/dev/null 2>&1; then
        ok "Redis štartnutý"
    else
        err "Redis sa nepodarilo štartnúť"
    fi
}

# ==============================================================================
# 9. SMOKE TEST — import app.main
# ==============================================================================
smoke_test() {
    cd "$ROOT"
    if python3 -c "from app.main import app; print('import OK')" 2>/dev/null; then
        ok "Smoke test: app.main sa importuje"
    else
        err "Smoke test ZLYHAL — app.main sa neimportuje"
        exit 1
    fi
}

# ==============================================================================
# 10. ŠTART UVICORN
# ==============================================================================
run_uvicorn() {
    ok "Spúšťam Uvicorn na http://0.0.0.0:8000"
    ok "Swagger: http://localhost:8000/docs"
    cd "$ROOT"
    exec python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# ==============================================================================
# MAIN
# ==============================================================================
echo "=================================================================="
echo "  CMEP / waste-platform — Master Repair & Start"
echo "=================================================================="
echo ""

fix_env
fix_config
fix_main
fix_memberships_prefix
archive_old_api
cleanup_bak

echo ""
echo ">>> Spúšťam služby..."
start_postgres
start_redis

echo ""
echo ">>> Smoke test..."
smoke_test

echo ""
echo ">>> Štart servera..."
run_uvicorn
