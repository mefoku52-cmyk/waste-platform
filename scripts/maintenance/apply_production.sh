#!/usr/bin/env bash
# Apply production fixes based on production_answers.txt
# Kazdy krok sa najprv pyta na podmienky. Ak nie su splnene, nic nerobi.
set -uo pipefail
cd ~/waste-platform

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"

echo "=========================================================="
echo "  APPLY PRODUCTION FIXES"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================================="
echo

# ---------- 1. JWT_SECRET ----------
echo "=== 1. JWT_SECRET ==="
if [ ! -f .env ]; then
  echo "[!] .env neexistuje. Vytvor ho z .env.example a spusti znova."
else
  CUR=$(grep -E "^JWT_SECRET=" .env | head -1 | cut -d= -f2- || true)
  if [ -n "$CUR" ] && [ "$CUR" != "change-me" ] && [ "$CUR" != "change-me-to-a-long-random-value" ] && [ ${#CUR} -ge 32 ]; then
    echo "[i] JWT_SECRET uz ma hodnotu (${#CUR} znakov). Nemenim."
  else
    if command -v python3 >/dev/null 2>&1; then
      NEW=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    elif command -v openssl >/dev/null 2>&1; then
      NEW=$(openssl rand -base64 48 | tr -d '\n=' | tr '+/' '-_')
    else
      echo "[!] Nemam python3 ani openssl na generovanie. Preskakujem."
      NEW=""
    fi
    if [ -n "$NEW" ]; then
      if grep -qE "^JWT_SECRET=" .env; then
        python3 - <<PY
import re
p=".env"
s=open(p).read()
s=re.sub(r"^JWT_SECRET=.*$", "JWT_SECRET=$NEW", s, flags=re.M)
open(p,"w").write(s)
PY
      else
        printf "\nJWT_SECRET=%s\n" "$NEW" >> .env
      fi
      echo "[x] JWT_SECRET zapisany do .env (${#NEW} znakov)"
      echo "    Nezapisujem do .env.production (podla odpovede 1b: n)"
    fi
  fi
fi
echo

# ---------- 2. Backup cez termux-job-scheduler ----------
echo "=== 2. Backup (termux-job-scheduler, daily 03:00) ==="
BK="scripts/backup/backup-db.sh"
if [ ! -f "$BK" ]; then
  echo "[!] $BK neexistuje. Preskakujem."
elif ! command -v termux-job-scheduler >/dev/null 2>&1; then
  echo "[!] termux-job-scheduler nie je v PATH. Preskakujem."
else
  echo "[i] $BK existuje."
  echo "[i] termux-job-scheduler je v PATH."
  echo "[i] NEregistrujem automaticky — najprv over, ze skript funguje samostatne:"
  echo "      bash $BK"
  echo
  echo "    Ak prejde, registruj manualne (daily = 86400000 ms):"
  echo "      termux-job-scheduler --script \$PWD/$BK --job-id waste-backup --period-ms 86400000 --network unmetered"
  echo "    Skontroluj:"
  echo "      termux-job-scheduler --job-id waste-backup --list"
  echo
  echo "[i] Presny cas 03:00 sa cez termux-job-scheduler neda nastavit —"
  echo "    je to periodicky interval, nie cron. Spusti sa raz za 24h"
  echo "    od momentu registracie. Ak chces presne 03:00, potrebujes crond."
fi
echo

# ---------- 3. nginx HTTP reverse proxy + rate limit ----------
echo "=== 3. nginx HTTP reverse proxy (port 8080) + rate limit ==="
NGX="$PREFIX/etc/nginx"
if [ ! -d "$NGX" ]; then
  echo "[!] $NGX neexistuje. nginx nie je nainstalovany. Preskakujem."
elif [ ! -f "$NGX/nginx.conf" ]; then
  echo "[!] $NGX/nginx.conf neexistuje. Preskakujem."
elif ! grep -qE "include.*conf\.d" "$NGX/nginx.conf"; then
  echo "[!] nginx.conf neobsahuje 'include conf.d'. Uprav manualne a spusti znova."
else
  mkdir -p "$NGX/conf.d"
  cat > "$NGX/conf.d/waste.conf" << 'NGINX'
# Waste Platform reverse proxy — HTTP only, port 8080 (localhost).
# SSL sa riesi na Cloudflare edge (ked bude tunel).

upstream waste_backend  { server 127.0.0.1:8000; }
upstream waste_frontend { server 127.0.0.1:3001; }

limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;

server {
    listen 127.0.0.1:8080;
    server_name _;

    client_max_body_size 20m;

    # Auth endpointy — rate limit 10 r/s, burst 20
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=20 nodelay;
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Ostatne API — bez rate limitu (app limiter to riesi)
    location /api/ {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health a metrics
    location = /health {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
    }
    location = /metrics {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
    }

    # Vsetko ostatne — frontend
    location / {
        proxy_pass http://waste_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX
  echo "[x] zapisane: $NGX/conf.d/waste.conf"
  echo "[i] Test syntaxe (bez spustenia): nginx -t"
  echo "[i] Start/restart: sv up nginx"
  echo
  echo "[!] Toto je HTTP-only na 127.0.0.1:8080. Bez externeho pristupu."
  echo "    Externy pristup vyzaduje Cloudflare tunel alebo verejnu IP + SSL."
fi
echo

# ---------- 4. cloudflared tunel ----------
echo "=== 4. cloudflared tunel ==="
if [ ! -f ~/.cloudflared/cert.pem ]; then
  echo "[!] ~/.cloudflared/cert.pem neexistuje — nie si prihlaseny v Cloudflare."
  echo "[i] Bez CF uctu tunel nenastavis."
  echo "[i] Postup, ked budes mat ucet:"
  echo "    1) cloudflared tunnel login"
  echo "    2) cloudflared tunnel create waste-platform"
  echo "    3) napis config ~/.cloudflared/config.yml:"
  echo "         tunnel: <ID>"
  echo "         credentials-file: ~/.cloudflared/<ID>.json"
  echo "         ingress:"
  echo "           - hostname: app.tvojadomena.sk"
  echo "             service: http://127.0.0.1:8080"
  echo "           - service: http_status:404"
  echo "    4) cloudflared tunnel route dns waste-platform app.tvojadomena.sk"
  echo "    5) sv up cloudflared"
  echo
  echo "[i] Preskakujem. Toto je interaktivne a vyzaduje tvoj CF ucet."
else
  echo "[OK] cert.pem existuje. Pokracuj manualne s config.yml."
fi
echo

# ---------- 5. make prod ----------
echo "=== 5. Makefile — pridat 'prod' target ==="
if [ ! -f Makefile ]; then
  echo "[!] Makefile neexistuje. Preskakujem."
elif grep -qE "^prod:" Makefile; then
  echo "[i] target 'prod' uz existuje. Nemenim."
else
  printf "\nprod:\n\tuvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4\n" >> Makefile
  echo "[x] pridany 'prod' target do Makefile:"
  echo "    prod:"
  echo "        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"
  echo
  echo "[i] Bez --reload, 4 workers. Ak mas ine preferencie (pocet workers),"
  echo "    uprav manualne."
fi
echo

# ---------- 6. Monitoring ----------
echo "=== 6. Monitoring ==="
echo "[i] Podla odpovede 7a: D — neskor. Preskakujem."
echo

# ---------- 7. .gitignore ----------
echo "=== 7. .gitignore — production_answers.txt ==="
if [ -f .gitignore ] && grep -q "^production_answers.txt$" .gitignore; then
  echo "[OK] uz je v .gitignore"
else
  echo "production_answers.txt" >> .gitignore
  echo "[x] pridane do .gitignore"
fi
echo

# ---------- Súhrn ----------
echo "=========================================================="
echo "  HOTOVO"
echo "=========================================================="
echo "Co bolo spravene:"
echo "  - JWT_SECRET vygenerovany a zapisany do .env"
echo "  - nginx conf.d/waste.conf zapisany (HTTP 8080)"
echo "  - Makefile: pridany 'prod' target"
echo "  - .gitignore: production_answers.txt"
echo
echo "Co treba manualne:"
echo "  - Backup: overit 'bash scripts/backup/backup-db.sh' a registrovat"
echo "    cez termux-job-scheduler (prikazy vyssie)"
echo "  - nginx: spustit 'nginx -t' a 'sv up nginx'"
echo "  - cloudflared: caka na CF ucet"
echo
echo "Zmeny v:"
git status --short .env Makefile .gitignore 2>/dev/null || true
echo "  (nginx config je mimo repa)"
