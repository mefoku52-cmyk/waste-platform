#!/usr/bin/env bash
set -u

ROOT="$HOME/waste-platform"
OUT="$ROOT/reports/authority-diagnostics-$(date +%Y%m%d-%H%M%S).txt"

mkdir -p "$ROOT/reports"

{
  echo "=================================================="
  echo "CMEP / waste-platform — AUTHORITY DIAGNOSTICS"
  echo "Cas: $(date -Iseconds)"
  echo "=================================================="

  echo
  echo "=== 1. FRONTEND PORT LISTENER ==="
  ss -ltnp 2>/dev/null | grep ':3001\b' || true

  echo
  echo "=== 2. NODE LISTENING SOCKETS ==="
  PID="$(pgrep -f 'next dev.*--port 3001' | head -1 || true)"

  if [ -n "$PID" ]; then
    echo "NEXT_PID=$PID"
    cat "/proc/$PID/net/tcp" 2>/dev/null || true
    cat "/proc/$PID/net/tcp6" 2>/dev/null || true
  else
    echo "NEXT_PID=NOT_FOUND"
  fi

  echo
  echo "=== 3. FRONTEND PAGE SOURCE ==="
  if [ -f "$ROOT/apps/web/src/app/page.tsx" ]; then
    sed -n '1,220p' "$ROOT/apps/web/src/app/page.tsx"
  else
    echo "page.tsx NOT_FOUND"
  fi

  echo
  echo "=== 4. FRONTEND ENV VARIABLE NAMES ==="
  for f in \
    "$ROOT/apps/web/.env.local" \
    "$ROOT/apps/web/.env.production" \
    "$ROOT/.env" \
    "$ROOT/.env.production"
  do
    if [ -f "$f" ]; then
      echo "--- $f ---"
      grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' "$f" |
        sed 's/=.*$/=REDACTED/' ||
        true
    fi
  done

  echo
  echo "=== 5. NEXT CONFIG ==="
  find "$ROOT/apps/web" -maxdepth 2 -type f \
    \( \
      -name 'next.config.*' \
      -o -name 'middleware.*' \
      -o -name 'instrumentation.*' \
    \) \
    -print 2>/dev/null |
    sort

  echo
  for f in \
    "$ROOT/apps/web/next.config.js" \
    "$ROOT/apps/web/next.config.mjs" \
    "$ROOT/apps/web/next.config.ts" \
    "$ROOT/apps/web/middleware.ts" \
    "$ROOT/apps/web/middleware.js"
  do
    if [ -f "$f" ]; then
      echo "--- $f ---"
      sed -n '1,260p' "$f"
    fi
  done

  echo
  echo "=== 6. COMPOSE ENV REFERENCES ==="
  cd "$ROOT"

  grep -nEi \
    'POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY|REGISTRY_IMAGE_PREFIX|env_file|environment:|\$\{' \
    docker-compose.yml \
    2>/dev/null ||
    true

  echo
  echo "=== 7. COMPOSE ENVIRONMENT FILES ==="

  for f in \
    "$ROOT/.env" \
    "$ROOT/.env.production" \
    "$ROOT/.env.example"
  do
    if [ -f "$f" ]; then
      echo "--- $f ---"

      for key in \
        POSTGRES_PASSWORD \
        JWT_REFRESH_SECRET_KEY \
        REGISTRY_IMAGE_PREFIX \
        POSTGRES_DB \
        POSTGRES_USER \
        DATABASE_URL \
        JWT_SECRET_KEY
      do
        if grep -qE "^${key}=" "$f"; then
          echo "$key=DEFINED"
        else
          echo "$key=MISSING"
        fi
      done
    fi
  done

  echo
  echo "=== 8. COMPOSE FILE HEADER ==="
  sed -n '1,180p' "$ROOT/docker-compose.yml" 2>/dev/null || true

  echo
  echo "=== 9. DEPLOYMENT ENV LOADING ==="

  for f in \
    "$ROOT/scripts/deploy.sh" \
    "$ROOT/scripts/production-recovery.sh" \
    "$ROOT/.production-release/r61-backup-20260903_104708/deploy.sh" \
    "$ROOT/.production-release/r61-backup-20260903_104708/production-recovery.sh"
  do
    if [ -f "$f" ]; then
      echo "--- $f ---"
      grep -nEi \
        'env-file|\.env|POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY|REGISTRY_IMAGE_PREFIX|docker compose|docker-compose' \
        "$f" 2>/dev/null |
        head -160 ||
        true
    fi
  done

  echo
  echo "=== 10. CURRENT SHELL ENV NAMES ONLY ==="

  env |
    grep -E '^(POSTGRES_PASSWORD|JWT_REFRESH_SECRET_KEY|REGISTRY_IMAGE_PREFIX)=' |
    sed 's/=.*$/=REDACTED/' ||
    echo "NONE_OF_REQUIRED_VARS_EXPORTED"

  echo
  echo "=== 11. COMPOSE CONFIG WITH EXPLICIT PRODUCTION ENV ==="

  COMPOSE_OUT="$ROOT/reports/.compose-production-check.tmp"

  if docker compose \
      --env-file "$ROOT/.env.production" \
      config >"$COMPOSE_OUT" 2>&1; then

    echo "COMPOSE_PRODUCTION_CONFIG=PASS"
  else
    echo "COMPOSE_PRODUCTION_CONFIG=FAIL"
    cat "$COMPOSE_OUT" 2>/dev/null || true
  fi

  rm -f "$COMPOSE_OUT" 2>/dev/null || true

  echo
  echo "=== 12. FRONTEND RAW TCP CHECK ==="

  if bash -c 'exec 3<>/dev/tcp/127.0.0.1/3001' 2>/dev/null; then
    echo "FRONTEND_TCP=PASS"
    exec 3>&-
  else
    echo "FRONTEND_TCP=FAIL"
  fi

  echo
  echo "=== 13. FINAL ==="
  echo "No files were modified except this diagnostic script and its report."
  echo "Report: $OUT"

} | tee "$OUT"
