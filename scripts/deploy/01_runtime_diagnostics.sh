#!/usr/bin/env bash
set -u

ROOT="$HOME/waste-platform"
OUT="$ROOT/reports/runtime-diagnostics-$(date +%Y%m%d-%H%M%S).txt"

mkdir -p "$ROOT/reports"

{
  echo "=================================================="
  echo "CMEP / waste-platform — RUNTIME DIAGNOSTICS"
  echo "Cas: $(date -Iseconds)"
  echo "=================================================="

  echo
  echo "=== 1. FRONTEND PROCES ==="
  ps -ef | grep -E 'next (dev|start)|node .*next' | grep -v grep || true

  echo
  echo "=== 2. FRONTEND PORT 3001 ==="
  ss -ltnp 2>/dev/null | grep ':3001\b' || true

  echo
  echo "--- localhost ---"
  curl -v --connect-timeout 3 --max-time 8 \
    http://127.0.0.1:3001/ \
    2>&1 || true

  echo
  echo "--- 0.0.0.0 ---"
  curl -v --connect-timeout 3 --max-time 8 \
    http://0.0.0.0:3001/ \
    2>&1 || true

  echo
  echo "=== 3. FRONTEND LOG PROCESU ==="
  PID="$(pgrep -f 'next dev.*--port 3001' | head -1 || true)"

  if [ -n "$PID" ]; then
    echo "NEXT_PID=$PID"
    echo "--- cmdline ---"
    tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null || true
    echo
    echo "--- cwd ---"
    readlink "/proc/$PID/cwd" 2>/dev/null || true
    echo
    echo "--- status ---"
    grep -E 'State|VmRSS|Threads' "/proc/$PID/status" 2>/dev/null || true
  else
    echo "NEXT_PID=NOT_FOUND"
  fi

  echo
  echo "=== 4. NODE / NPM ==="
  node --version 2>&1 || true
  npm --version 2>&1 || true
  cd "$ROOT/apps/web"
  npm run typecheck 2>&1 || true

  echo
  echo "=== 5. NEXT BUILD CHECK ==="
  npm run build 2>&1 || true

  echo
  echo "=== 6. BACKEND ==="
  curl -sS --max-time 5 \
    http://127.0.0.1:8001/health \
    2>&1 || true

  echo
  echo "=== 7. BACKEND PORT ==="
  ss -ltnp 2>/dev/null | grep ':8001\b' || true

  echo
  echo "=== 8. POSTGRES ==="
  pgrep -a postgres 2>/dev/null || true
  ss -ltnp 2>/dev/null | grep ':5432\b' || true

  echo
  echo "=== 9. DOCKER CLI ==="
  docker --version 2>&1 || true
  docker compose version 2>&1 || true

  echo
  echo "=== 10. DOCKER DAEMON ==="
  docker info 2>&1 || true

  echo
  echo "=== 11. DOCKER SOCKET ==="
  ls -la \
    /data/data/com.termux/files/usr/var/run/docker.sock \
    2>&1 || true

  echo
  echo "=== 12. QEMU ==="
  pgrep -a qemu-system-x86_64 2>/dev/null || true

  echo
  echo "=== 13. QEMU DOCKER SCRIPTS ==="
  ls -l \
    "$HOME/alpine-vm/qemu-docker/boot-docker.sh" \
    "$HOME/alpine-vm/qemu-docker/boot-docker-api.sh" \
    "$HOME/START_CMEP_DOCKER.sh" \
    "$HOME/boot-docker.sh" \
    2>&1 || true

  echo
  echo "=== 14. COMPOSE CONFIG VALIDATION ==="
  cd "$ROOT"

  if docker compose config >/tmp/cmep-compose-check.txt 2>&1; then
    echo "COMPOSE_CONFIG=OK"
  else
    echo "COMPOSE_CONFIG=FAIL"
    cat /tmp/cmep-compose-check.txt
  fi

  echo
  echo "=== HOTOVO ==="
  echo "Report: $OUT"

} | tee "$OUT"
