#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$HOME/waste-platform"
OUT="$ROOT/reports/production-readiness-$(date +%Y%m%d-%H%M%S).txt"

mkdir -p "$ROOT/reports"

{
  echo "=================================================="
  echo "CMEP / waste-platform — PRODUCTION READINESS INVENTORY"
  echo "Cas: $(date -Iseconds)"
  echo "=================================================="

  echo
  echo "=== 1. KOREN PROJEKTU A GIT ==="
  printf 'Projekt: '
  realpath "$ROOT" 2>&1 || true

  echo "--- branch ---"
  git -C "$ROOT" branch --show-current 2>&1 || true

  echo "--- status ---"
  git -C "$ROOT" status --short 2>&1 || true

  echo "--- poslednych 10 commitov ---"
  git -C "$ROOT" log --oneline -10 2>&1 || true

  echo "--- remote ---"
  git -C "$ROOT" remote -v 2>&1 || true

  echo "--- tracked deployment/config files ---"
  git -C "$ROOT" ls-files 2>/dev/null |
    grep -Ei '(^|/)(docker-compose|compose|Dockerfile|\.env|deploy|production|caddy|traefik|nginx|alembic)' ||
    true

  echo
  echo "=== 2. RUNTIME SLUZBY ==="

  echo "--- porty 3001 / 8001 / 5432 ---"
  ss -ltn 2>/dev/null |
    grep -E ':(3001|8001|5432)\b' ||
    true

  echo "--- procesy ---"
  ps -ef 2>/dev/null |
    grep -Ei 'uvicorn|next dev|next start|postgres|docker|proot|alpine|qemu' |
    grep -v grep ||
    true

  echo "--- backend health ---"
  /data/data/com.termux/files/usr/bin/curl \
    -sS \
    --max-time 5 \
    http://127.0.0.1:8001/health 2>&1 ||
    true

  echo
  echo "--- frontend HTTP ---"
  /data/data/com.termux/files/usr/bin/curl \
    -sS \
    -o /dev/null \
    -w 'HTTP %{http_code}\n' \
    --max-time 5 \
    http://127.0.0.1:3001/ 2>&1 ||
    true

  echo
  echo "=== 3. DOCKER A COMPOSE ==="

  echo "--- docker command ---"
  command -v docker 2>&1 || true
  docker --version 2>&1 || true

  echo "--- docker compose ---"
  docker compose version 2>&1 || true

  echo "--- docker-compose command ---"
  command -v docker-compose 2>&1 || true
  docker-compose --version 2>&1 || true

  echo "--- containers ---"
  docker ps -a 2>&1 || true

  echo
  echo "=== 4. ALPINE / PROOT / QEMU ==="

  echo "--- proot-distro ---"
  command -v proot-distro 2>&1 || true
  proot-distro list 2>&1 || true

  echo "--- relevantne cesty v HOME ---"
  find "$HOME" -maxdepth 3 \
    \( \
      -iname '*alpine*' \
      -o -iname '*proot*' \
      -o -iname '*qemu*' \
      -o -iname '*docker*' \
    \) \
    2>/dev/null |
    sort ||
    true

  echo
  echo "=== 5. DEPLOYMENT SUBORY ==="

  find "$ROOT" -maxdepth 4 -type f \
    \( \
      -iname 'docker-compose*.yml' \
      -o -iname 'compose*.yml' \
      -o -iname 'Dockerfile*' \
      -o -iname '*deploy*.sh' \
      -o -iname '*production*.sh' \
      -o -iname '*release*.sh' \
    \) \
    2>/dev/null |
    sort ||
    true

  echo
  echo "=== 6. KONFIGURACIA BEZ HODNOT TAJOMSTIEV ==="

  for f in \
    "$ROOT/.env" \
    "$ROOT/.env.production" \
    "$ROOT/.env.example" \
    "$ROOT/apps/web/.env.local"
  do
    if [ -f "$f" ]; then
      echo "--- $f ---"
      sed -n \
        '/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=/s/=.*$/=REDACTED/p' \
        "$f" ||
        true
    fi
  done

  echo
  echo "=== 7. DATABAZA A MIGRACIE ==="

  echo "--- alembic.ini URL (redacted) ---"
  sed -n \
    '/^sqlalchemy.url[[:space:]]*=/s/=.*$/=REDACTED/p' \
    "$ROOT/alembic.ini" 2>/dev/null ||
    true

  echo "--- alembic versions ---"
  if [ -d "$ROOT/migrations/versions" ]; then
    find "$ROOT/migrations/versions" \
      -maxdepth 1 \
      -type f \
      -name '*.py' \
      -printf '%f\n' \
      2>/dev/null |
      sort ||
      true
  fi

  echo "--- SQLite databazy ---"
  find "$ROOT" \
    -maxdepth 4 \
    -type f \
    \( \
      -name '*.db' \
      -o -name '*.sqlite' \
      -o -name '*.sqlite3' \
    \) \
    -printf '%s bytes  %p\n' \
    2>/dev/null ||
    true

  echo
  echo "=== 8. BUILD A TEST PRIKAZY Z PROJEKTU ==="

  echo "--- Makefile targets ---"
  grep -E '^[A-Za-z0-9_.-]+:' \
    "$ROOT/Makefile" 2>/dev/null |
    head -80 ||
    true

  echo "--- package scripts ---"
  python3 -c "
import json
from pathlib import Path

p = Path('$ROOT/apps/web/package.json')

if p.is_file():
    print(json.dumps(
        json.loads(p.read_text()).get('scripts', {}),
        indent=2
    ))
else:
    print('package.json: NOT_FOUND')
" 2>&1 || true

  echo "--- pyproject relevantne riadky ---"
  grep -nEi \
    'pytest|ruff|mypy|uvicorn|alembic|sqlalchemy' \
    "$ROOT/pyproject.toml" 2>/dev/null |
    head -80 ||
    true

  echo
  echo "=== HOTOVO ==="
  echo "Report: $OUT"

} | tee "$OUT"
