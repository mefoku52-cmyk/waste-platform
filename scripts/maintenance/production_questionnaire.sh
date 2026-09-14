#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

OUT="production_answers.txt"
: > "$OUT"

w() { echo "$@" | tee -a "$OUT"; }

w "=========================================================="
w "  PRODUCTION QUESTIONNAIRE"
w "  $(date '+%Y-%m-%d %H:%M:%S')"
w "  Vystup: $(pwd)/$OUT"
w "=========================================================="
w ""

# ---------------- KONTEXT (auto-collected, read-only) ----------------
w "## KONTEXT (auto, read-only)"
w ""

w "### .env — vybrane kluce (SECRET/PASSWORD/TOKEN maskovane)"
if [ -f .env ]; then
  grep -E "^(APP_DOMAIN|API_DOMAIN|APP_HOST|REDIS_HOST|CORS_ORIGINS|NEXT_PUBLIC|APP_ENV)=" .env 2>/dev/null >> "$OUT" || true
  echo "" >> "$OUT"
else
  w "[i] .env neexistuje"
fi
w ""

w "### .env.production — existuje a ma JWT_SECRET?"
if [ -f .env.production ]; then
  if grep -q "^JWT_SECRET=" .env.production 2>/dev/null; then
    n=$(grep "^JWT_SECRET=" .env.production | cut -d= -f2- | wc -c)
    w "[OK] .env.production ma JWT_SECRET (dlzka ~$n)"
  else
    w "[i] .env.production existuje, ale bez JWT_SECRET"
  fi
else
  w "[i] .env.production neexistuje"
fi
w ""

w "### Makefile (cely)"
if [ -f Makefile ]; then cat Makefile >> "$OUT"; else echo "[i] Makefile neexistuje" >> "$OUT"; fi
w ""

w "### scripts/backup/backup-db.sh (prvych 50 riadkov)"
if [ -f scripts/backup/backup-db.sh ]; then head -50 scripts/backup/backup-db.sh >> "$OUT"; else echo "[i] neexistuje" >> "$OUT"; fi
w ""

w "### scripts/backup/cron-example.txt"
if [ -f scripts/backup/cron-example.txt ]; then cat scripts/backup/cron-example.txt >> "$OUT"; else echo "[i] neexistuje" >> "$OUT"; fi
w ""

w "### app/shared/presentation/metrics_router.py"
if [ -f app/shared/presentation/metrics_router.py ]; then cat app/shared/presentation/metrics_router.py >> "$OUT"; else echo "[i] neexistuje" >> "$OUT"; fi
w ""

w "### Cloudflared stav"
if [ -f ~/.cloudflared/cert.pem ]; then w "[OK] ~/.cloudflared/cert.pem existuje (prihlaseny)"; else w "[i] ~/.cloudflared/cert.pem neexistuje (neprihlaseny)"; fi
w ""

w "### termux-job-scheduler / crond pritomnost"
if command -v termux-job-scheduler >/dev/null 2>&1; then w "[OK] termux-job-scheduler je v PATH"; else w "[i] termux-job-scheduler nie je v PATH"; fi
if command -v crond >/dev/null 2>&1; then w "[OK] crond je v PATH"; else w "[i] crond nie je v PATH"; fi
if command -v crontab >/dev/null 2>&1; then w "[OK] crontab je v PATH"; else w "[i] crontab nie je v PATH"; fi
w ""

w "### Sentry / Prometheus v dependencies"
grep -iE "sentry|prometheus" pyproject.toml requirements*.txt 2>/dev/null >> "$OUT" || echo "[i] ziadny sentry/prometheus v pyproject/requirements" >> "$OUT"
w ""

w "## ODPOVEDE"
w ""

# ---------------- OTAZKY ----------------
ask() {
  local q="$1"
  local default="${2:-}"
  echo ""
  echo "----------------------------------------------------------"
  echo "$q"
  echo "$q" >> "$OUT"
  if [ -n "$default" ]; then
    echo -n "[Enter = $default] > "
  else
    echo -n "> "
  fi
  read -r ans || true
  ans="${ans:-$default}"
  echo "ODPOVED: $ans" | tee -a "$OUT"
  echo "" >> "$OUT"
}

echo ""
echo "=========================================================="
echo "  ZACIATOK OTAZOK"
echo "=========================================================="

ask "1a. JWT_SECRET — vygenerovat 64-znakovy nahodny a zapisat do .env? (y/n)" "y"
ask "1b. Zapisat aj do .env.production? (y/n)" "n"

ask "2a. Backup — termux-job-scheduler alebo crond? [ts/crond]" "ts"
ask "2b. Frekvencia? [hourly/daily/weekly/monthly]" "daily"
ask "2c. Cas spustenia (HH:MM)?" "03:00"

ask "3a. Architektura: 1=cloudflared-bez-SSL-nginx, 2=priamy-SSL-nginx [1/2]" "1"
ask "3b. Realna domena (napr. app.example.sk) alebo 'ziadna'?" "ziadna"

ask "4a. Cloudflare — mas ucet a domenu? [ano/nie/quick]" "nie"

ask "5a. Rate limit — requesty za sekundu na IP?" "10"
ask "5b. Burst?" "20"
ask "5c. Len /api/v1/auth/* alebo vsetky cesty? [auth/all]" "auth"

ask "6. Makefile — vidis ho v kontexte vyssie. Mam pridat 'make prod' bez --reload? (y/n)" "y"

ask "7a. Monitoring — A=Sentry, B=Prometheus+Grafana, C=log-alert, D=neskor [A/B/C/D]" "D"
ask "7b. Ak A, Sentry DSN (alebo 'ziadny')?" "ziadny"

echo ""
echo "=========================================================="
echo "  HOTOVO"
echo "=========================================================="
echo "Subor: $(pwd)/$OUT"
echo "Posli jeho obsah spat."
echo ""
echo "POZOR: $OUT moze obsahovat citlive udaje (env kluce)."
echo "Necommituj ho. Je v .gitignore? Skontroluj:"
if grep -q "^production_answers.txt$" .gitignore 2>/dev/null; then
  echo "[OK] je v .gitignore"
else
  echo "[i] NIE je v .gitignore. Pridaj:"
  echo "    echo 'production_answers.txt' >> .gitignore"
fi
