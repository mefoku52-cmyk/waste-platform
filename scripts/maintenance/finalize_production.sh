#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
NGX="$PREFIX/etc/nginx"
FAIL=0

echo "=========================================================="
echo "  FINALIZE PRODUCTION"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================================="
echo

# ---------- 1. Nginx start ----------
echo "=== 1. Nginx start ==="
if pgrep -x nginx >/dev/null 2>&1; then
  echo "[i] nginx uz bezi (PID: $(pgrep -x nginx | tr '\n' ' '))"
else
  echo "[i] nginx nebezi. Spustam cez sv."
  sv up nginx
  sleep 2
  if pgrep -x nginx >/dev/null 2>&1; then
    echo "[x] nginx bezi (PID: $(pgrep -x nginx | tr '\n' ' '))"
  else
    echo "[!] nginx sa nespustil. Skontroluj:"
    echo "    sv status nginx"
    echo "    tail -30 $PREFIX/var/log/sv/nginx/current"
    FAIL=1
  fi
fi
echo

# ---------- 2. Test backend / frontend portov ----------
echo "=== 2. Stav backend / frontend ==="
for port in 8000 3001; do
  if (echo > /dev/tcp/127.0.0.1/$port) 2>/dev/null; then
    echo "[OK] port $port odpoveda"
  else
    echo "[i] port $port neodpoveda (backend/frontend nebezi)"
  fi
done
echo

# ---------- 3. Curl na /health ----------
echo "=== 3. Test http://127.0.0.1:8080/health ==="
RESP=$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health 2>&1 || echo "ERR")
echo "[i] HTTP kod: $RESP"
case "$RESP" in
  200) echo "[OK] backend odpoveda cez nginx." ;;
  502|503) echo "[i] nginx bezi, ale backend neodpoveda. Spusti backend: make dev" ;;
  ERR|000) echo "[!] nginx neodpoveda na 8080. Pozri sv status nginx."; FAIL=1 ;;
  *) echo "[i] neocekavany kod: $RESP" ;;
esac
echo

# ---------- 4. Backup job (spravny job-id = int) ----------
echo "=== 4. termux-job-scheduler: backup (job-id 9001) ==="
BK="$PWD/scripts/backup/backup-db.sh"
JOB_ID=9001
if [ ! -x "$BK" ]; then
  echo "[!] $BK nie je spustitelny. chmod +x a spusti znova."
  FAIL=1
elif ! command -v termux-job-scheduler >/dev/null 2>&1; then
  echo "[!] termux-job-scheduler nie je v PATH."
  FAIL=1
else
  echo "[i] Registrujem: --job-id $JOB_ID --period-ms 86400000 --network unmetered --persisted true"
  if termux-job-scheduler -s "$BK" --job-id "$JOB_ID" --period-ms 86400000 --network unmetered --persisted true 2>&1; then
    echo "[x] job zaregistrovany."
  else
    echo "[!] registracia zlyhala. Pozri vystup vyssie."
    FAIL=1
  fi
  echo
  echo "[i] Zoznam pending jobov:"
  termux-job-scheduler --pending 2>&1 | head -20 || true
  echo
  echo "[i] Ak chces job zrusit: termux-job-scheduler --cancel $JOB_ID"
  echo "[i] Presne 03:00 sa neda — je to interval, spusti sa 24h od registracie."
fi
echo

# ---------- 5. audit_report.txt do .gitignore ----------
echo "=== 5. .gitignore: audit_report.txt ==="
if [ -f .gitignore ] && grep -q "^audit_report.txt$" .gitignore; then
  echo "[i] uz je v .gitignore"
else
  echo "audit_report.txt" >> .gitignore
  echo "[x] pridane"
fi
echo

# ---------- 6. git add skripty ----------
echo "=== 6. git add novych skriptov ==="
git add \
  scripts/maintenance/audit_production.sh \
  scripts/maintenance/production_questionnaire.sh \
  scripts/maintenance/apply_production.sh \
  scripts/maintenance/apply_production_v2.sh \
  scripts/maintenance/finalize_production.sh \
  scripts/maintenance/finish_cleanup.sh \
  scripts/maintenance/cleanup.sh \
  scripts/maintenance/diag.sh \
  scripts/maintenance/fix_datetime.sh \
  scripts/maintenance/fix_duplicates.sh \
  scripts/maintenance/fix_init.sh \
  2>/dev/null || true
git add .gitignore Makefile 2>/dev/null || true
echo "[i] git status:"
git status --short
echo

# ---------- 7. commit ----------
echo "=== 7. Commit ==="
if git diff --cached --quiet; then
  echo "[i] nic na commit."
else
  git commit -m "chore: production scaffold — JWT, nginx conf.d, backup job, maintenance scripts" || {
    echo "[!] commit zlyhal (pre-commit?)."
    FAIL=1
  }
  git log --oneline -3
fi
echo

# ---------- 8. Dynamicky suhrn ----------
echo "=========================================================="
echo "  SÚHRN"
echo "=========================================================="
echo "JWT_SECRET:        $([ -f .env ] && grep -qE '^JWT_SECRET=.{32,}' .env && echo OK || echo CHYBA)"
echo "Makefile prod:     $(grep -qE '^prod:' Makefile 2>/dev/null && echo OK || echo CHYBA)"
echo "nginx.conf:        $([ -f $NGX/nginx.conf.waste.bak ] && echo 'upraveny' || echo 'nezmeneny')"
echo "conf.d/waste.conf: $([ -f $NGX/conf.d/waste.conf ] && echo OK || echo CHYBA)"
echo "nginx bezi:        $(pgrep -x nginx >/dev/null && echo OK || echo NIE)"
echo "backup script:     $([ -x $PWD/scripts/backup/backup-db.sh ] && echo OK || echo CHYBA)"
echo "backup job:        $(termux-job-scheduler --pending 2>/dev/null | grep -q '9001' && echo 'OK (job-id 9001)' || echo 'neregistrovany')"
echo "cloudflared:       $([ -f ~/.cloudflared/cert.pem ] && echo OK || echo 'caka na CF ucet')"
echo
if [ "$FAIL" = "0" ]; then
  echo "Vsetko dokoncene."
else
  echo "Nieco zlyhalo. Pozri [!] riadky."
fi
