#!/usr/bin/env bash
set -u

ROOT="$HOME/waste-platform"
OUT="$ROOT/reports/runtime-gate-$(date +%Y%m%d-%H%M%S).txt"

mkdir -p "$ROOT/reports"

{
  echo "=================================================="
  echo "CMEP / waste-platform — RUNTIME GATE"
  echo "Cas: $(date -Iseconds)"
  echo "=================================================="

  echo
  echo "=== 1. BACKEND ==="
  if curl -fsS --max-time 5 http://127.0.0.1:8001/health; then
    echo
    echo "BACKEND_HEALTH=PASS"
  else
    echo
    echo "BACKEND_HEALTH=FAIL"
  fi

  echo
  echo "=== 2. FRONTEND PROCESS ==="
  if pgrep -af 'next (dev|start).*3001' 2>/dev/null; then
    echo "FRONTEND_PROCESS=PASS"
  else
    echo "FRONTEND_PROCESS=FAIL"
  fi

  echo
  echo "=== 3. FRONTEND HTTP ==="

  FRONTEND_HEADERS="$ROOT/reports/.frontend_headers.tmp"

  if curl \
      -sS \
      -D "$FRONTEND_HEADERS" \
      -o /dev/null \
      --connect-timeout 5 \
      --max-time 15 \
      http://127.0.0.1:3001/; then

    echo "FRONTEND_HTTP=PASS"
    echo "--- headers ---"
    cat "$FRONTEND_HEADERS" 2>/dev/null || true
  else
    echo "FRONTEND_HTTP=FAIL"
  fi

  rm -f "$FRONTEND_HEADERS" 2>/dev/null || true

  echo
  echo "=== 4. FRONTEND DASHBOARD ==="

  DASHBOARD_HEADERS="$ROOT/reports/.dashboard_headers.tmp"

  if curl \
      -sS \
      -D "$DASHBOARD_HEADERS" \
      -o /dev/null \
      --connect-timeout 5 \
      --max-time 15 \
      http://127.0.0.1:3001/dashboard; then

    echo "DASHBOARD_HTTP=PASS"
    grep -Ei '^(HTTP/|location:|content-type:)' \
      "$DASHBOARD_HEADERS" 2>/dev/null || true
  else
    echo "DASHBOARD_HTTP=FAIL"
  fi

  rm -f "$DASHBOARD_HEADERS" 2>/dev/null || true

  echo
  echo "=== 5. FRONTEND BUILD ARTIFACT ==="

  if [ -f "$ROOT/apps/web/.next/BUILD_ID" ]; then
    echo "NEXT_BUILD=PASS"
    printf 'BUILD_ID='
    cat "$ROOT/apps/web/.next/BUILD_ID"
    echo
  else
    echo "NEXT_BUILD=FAIL"
    echo "Missing apps/web/.next/BUILD_ID"
  fi

  echo
  echo "=== 6. POSTGRES PROCESS ==="

  if pgrep -af postgres 2>/dev/null; then
    echo "POSTGRES_PROCESS=PASS"
  else
    echo "POSTGRES_PROCESS=FAIL"
  fi

  echo
  echo "=== 7. POSTGRES TCP ==="

  if bash -c 'exec 3<>/dev/tcp/127.0.0.1/5432' 2>/dev/null; then
    echo "POSTGRES_TCP=PASS"
    exec 3>&-
  else
    echo "POSTGRES_TCP=FAIL"
  fi

  echo
  echo "=== 8. DOCKER CLI ==="

  docker --version 2>&1 || true
  docker compose version 2>&1 || true

  echo
  echo "=== 9. DOCKER SOCKET ==="

  DOCKER_SOCK="/data/data/com.termux/files/usr/var/run/docker.sock"

  if [ -S "$DOCKER_SOCK" ]; then
    echo "DOCKER_SOCKET=PASS"
    ls -l "$DOCKER_SOCK"
  else
    echo "DOCKER_SOCKET=FAIL"
    echo "Missing: $DOCKER_SOCK"
  fi

  echo
  echo "=== 10. DOCKER DAEMON ==="

  if docker info >/dev/null 2>&1; then
    echo "DOCKER_DAEMON=PASS"
  else
    echo "DOCKER_DAEMON=FAIL"
    docker info 2>&1 || true
  fi

  echo
  echo "=== 11. QEMU ==="

  if pgrep -af qemu-system-x86_64 2>/dev/null; then
    echo "QEMU=PASS"
  else
    echo "QEMU=STOPPED"
  fi

  echo
  echo "=== 12. COMPOSE CONFIG ==="

  COMPOSE_OUT="$ROOT/reports/.compose_config.tmp"

  if docker compose config >"$COMPOSE_OUT" 2>&1; then
    echo "COMPOSE_CONFIG=PASS"
  else
    echo "COMPOSE_CONFIG=FAIL"
    cat "$COMPOSE_OUT" 2>/dev/null || true
  fi

  rm -f "$COMPOSE_OUT" 2>/dev/null || true

  echo
  echo "=== 13. FINAL GATE ==="

  FAIL=0

  if ! curl -fsS --max-time 5 \
      http://127.0.0.1:8001/health >/dev/null 2>&1; then
    FAIL=1
  fi

  if [ ! -f "$ROOT/apps/web/.next/BUILD_ID" ]; then
    FAIL=1
  fi

  if ! pgrep -f 'next (dev|start).*3001' >/dev/null 2>&1; then
    FAIL=1
  fi

  if [ "$FAIL" -eq 0 ]; then
    echo "APPLICATION_RUNTIME_GATE=PASS"
  else
    echo "APPLICATION_RUNTIME_GATE=REVIEW"
  fi

  echo
  echo "=== HOTOVO ==="
  echo "Report: $OUT"

} | tee "$OUT"
