#!/usr/bin/env bash
# Production readiness audit — READ ONLY. Nič nespúšťa, nič nemodifikuje.
set -uo pipefail
cd ~/waste-platform

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"

echo "======================================================"
echo "  PRODUCTION READINESS AUDIT"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"
echo

# --- 1. Reverse proxy ---
echo "=== 1. Reverse proxy (nginx) ==="
if pgrep -x nginx >/dev/null; then
  echo "[OK] nginx beží (PID: $(pgrep -x nginx | tr '\n' ' '))"
else
  echo "[CHYBA] nginx nebeží"
fi
echo "--- configy ---"
find "$PREFIX/etc/nginx" -maxdepth 3 -type f -name "*.conf" 2>/dev/null | head -20 || echo "[i] žiadne"
echo "--- proxy_pass / upstream ---"
grep -rn "proxy_pass\|upstream" "$PREFIX/etc/nginx/" 2>/dev/null | head -20 || echo "[i] nič"
echo "--- SSL / 443 ---"
grep -rln "ssl_certificate\|listen.*443" "$PREFIX/etc/nginx/" 2>/dev/null || echo "[CHYBA] žiadny SSL cert / 443"
echo

# --- 2. Doména a DNS ---
echo "=== 2. Doména a DNS ==="
grep -iE "^[A-Z_]*DOMAIN|^[A-Z_]*HOST|^CORS_ORIGINS|^NEXT_PUBLIC" .env 2>/dev/null | sed 's/=.*/=<...>/' || echo "[i] žiadne doménové premenné v .env"
grep -rn "server_name" "$PREFIX/etc/nginx/" 2>/dev/null || echo "[i] žiadny server_name v nginx"
echo "--- cloudflared tunel ---"
ls ~/.cloudflared/*.yml ~/.cloudflared/*.yaml 2>/dev/null && grep -n "hostname\|service" ~/.cloudflared/*.yml 2>/dev/null | head -10 || echo "[i] žiadny cloudflared tunel config"
echo

# --- 3. Produkčné buildy ---
echo "=== 3. Produkčné buildy ==="
for pkg in package.json apps/web/package.json; do
  if [ -f "$pkg" ]; then
    echo "--- $pkg scripts ---"
    python -c "import json,sys; d=json.load(open('$pkg')); [print(f'  {k}: {v}') for k,v in d.get('scripts',{}).items()]" 2>/dev/null
  fi
done
[ -d apps/web/.next ] && echo "[OK] apps/web/.next existuje (build prebehol)" || echo "[CHYBA] apps/web/.next neexistuje — build ešte nebol"
echo "--- hľadám --reload (dev mód) v scripts ---"
grep -rn "uvicorn.*--reload\|next dev\|npm run dev" scripts/ Makefile* Procfile* 2>/dev/null || echo "[i] žiadny --reload v scripts/"
echo

# --- 4. Produkčné .env ---
echo "=== 4. Produkčné .env ==="
if [ -f .env ]; then
  echo "[i] .env existuje"
  APP_ENV=$(grep -E "^APP_ENV=" .env | cut -d= -f2)
  echo "    APP_ENV=$APP_ENV"
  JWT=$(grep -E "^JWT_SECRET=" .env | cut -d= -f2-)
  if [ -z "$JWT" ] || [ "$JWT" = "change-me" ] || [ ${#JWT} -lt 32 ]; then
    echo "[CHYBA] JWT_SECRET slabý/placeholder (${#JWT} znakov)"
  else
    echo "[OK] JWT_SECRET: ${#JWT} znakov"
  fi
  DB=$(grep -E "^DATABASE_URL=" .env | cut -d= -f2-)
  if echo "$DB" | grep -qE "change-me|:password@|://[^:]*@"; then
    echo "[CHYBA] DATABASE_URL bez hesla / placeholder"
  else
    echo "[i] DATABASE_URL má heslo"
  fi
else
  echo "[CHYBA] .env neexistuje"
fi
[ -f .env.production ] && echo "[OK] .env.production existuje" || echo "[i] .env.production neexistuje"
echo

# --- 5. Migrácie ---
echo "=== 5. Alembic migrácie ==="
echo "--- alembic current ---"
alembic current 2>&1 | tail -3
echo "--- alembic heads ---"
alembic heads 2>&1 | tail -3
echo

# --- 6. Monitoring ---
echo "=== 6. Monitoring ==="
grep -rln "sentry_sdk\|from sentry\|prometheus_client\|datadog\|newrelic" app/ pyproject.toml requirements*.txt 2>/dev/null || echo "[CHYBA] žiadny monitoring framework v kóde"
echo "--- /metrics endpoint ---"
grep -rn "@.*get(\"/metrics\"\|/metrics" app/ 2>/dev/null | head -5 || echo "[i] žiadny /metrics"
echo "--- /health endpointy ---"
grep -rn "/health\b\|/healthz\|/readyz" app/ 2>/dev/null | head -10
echo

# --- 7. Backupy DB ---
echo "=== 7. Backupy DB ==="
find . -name "*backup*.sh" 2>/dev/null | head -10 || true
grep -rln "pg_dump\|pg_basebackup" . 2>/dev/null | head -10 || echo "[CHYBA] žiadny pg_dump v projekte"
ls -la ~/backups 2>/dev/null || echo "[i] ~/backups neexistuje"
echo "--- cron / termux-job-scheduler ---"
crontab -l 2>/dev/null | grep -i "backup\|pg_dump" || echo "[i] žiadny cron job pre backup"
echo

# --- 8. Rate limiting na proxy ---
echo "=== 8. Rate limiting na proxy ==="
echo "--- nginx ---"
grep -rn "limit_req\|limit_conn" "$PREFIX/etc/nginx/" 2>/dev/null || echo "[CHYBA] žiadny limit_req/limit_conn v nginx"
echo "--- cloudflared ---"
grep -rn "limit\|rate" ~/.cloudflared/ 2>/dev/null | head -5 || echo "[i] cloudflared bez rate limiting konfigu"
echo "--- aplikácia (vlastný limiter) ---"
ls app/shared/infrastructure/rate_limit*.py 2>/dev/null || echo "[i] žiadny app limiter"
echo

# --- 9. Logy s rotáciou ---
echo "=== 9. Logy s rotáciou ==="
echo "--- runit svlogd (rotácia riešená cez tai64 formát) ---"
for svc in postgres nginx cloudflared; do
  d="$PREFIX/var/log/sv/$svc"
  if [ -d "$d" ]; then
    n=$(find "$d" -type f -name "@*" 2>/dev/null | wc -l)
    echo "[i] $svc: $n rotovaných log súborov v $d"
  fi
done
echo "--- logrotate ---"
ls "$PREFIX/etc/logrotate.d/" 2>/dev/null | head -20 || echo "[i] žiadny logrotate.d"
echo "--- aplikačné log súbory v projekte ---"
find . -name "*.log" -not -path "./.git/*" 2>/dev/null | head -10
echo

# --- 10. Testy a coverage ---
echo "=== 10. Testy a coverage ==="
echo "--- počet testovacích súborov ---"
find tests -name "test_*.py" 2>/dev/null | wc -l
echo "--- pytest s coverage (toto chvíľu trvá) ---"
pytest -q --cov=app --cov-report=term-missing 2>&1 | tail -25
echo

# --- Súhrn ---
echo "======================================================"
echo "  SÚHRN"
echo "======================================================"
echo "[OK]     — máš a je to v poriadku"
echo "[CHYBA]  — nemáš alebo je v zlom stave"
echo "[i]      — neutrálna informácia, posúď sám"
echo
echo "Odporúčaný ďalší krok: prejdi si [CHYBA] riadky zhora dole."
echo "Nič sa nemodifikovalo. Skript je read-only."
