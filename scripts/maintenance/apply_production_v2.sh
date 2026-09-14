#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
NGX="$PREFIX/etc/nginx"
FAIL=0

echo "=========================================================="
echo "  APPLY PRODUCTION v2"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================================="
echo

# ---------- 1. nginx.conf uprava ----------
echo "=== 1. nginx.conf: include conf.d + default server na 8081 ==="
if [ ! -f "$NGX/nginx.conf" ]; then
  echo "[!] $NGX/nginx.conf neexistuje. Preskakujem."
  FAIL=1
elif [ -f "$NGX/nginx.conf.waste.bak" ]; then
  echo "[i] zaloha nginx.conf.waste.bak uz existuje. Nemenim znovu."
else
  python3 - "$NGX/nginx.conf" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()

# zaloha
open(p + ".waste.bak", "w").write(s)

# 1) default server port 8080 -> 8081
if "listen       8080;" in s:
    s = s.replace("listen       8080;", "listen       8081;", 1)
    print("[x] listen 8080 -> 8081 (default server)")
else:
    print("[!] nenasiel 'listen       8080;' — nemenim port")

# 2) include conf.d pred koniec http bloku
if "include conf.d/*.conf;" not in s:
    idx = s.rfind("\n}")
    if idx == -1:
        print("[!] nenasiel koniec http bloku")
    else:
        s = s[:idx] + "\n    include conf.d/*.conf;\n" + s[idx:]
        print("[x] include conf.d/*.conf; pridany do http bloku")
else:
    print("[i] include conf.d uz existuje")

open(p, "w").write(s)
PY
fi
echo

# ---------- 2. zapis waste.conf ----------
echo "=== 2. conf.d/waste.conf ==="
mkdir -p "$NGX/conf.d"
cat > "$NGX/conf.d/waste.conf" << 'NGINX'
# Waste Platform reverse proxy — HTTP only, port 8080.
# SSL sa riesi na Cloudflare edge (ked bude tunel).

upstream waste_backend  { server 127.0.0.1:8000; }
upstream waste_frontend { server 127.0.0.1:3001; }

limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;

server {
    listen 127.0.0.1:8080;
    server_name _;

    client_max_body_size 20m;

    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=20 nodelay;
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /health {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
    }
    location = /metrics {
        proxy_pass http://waste_backend;
        proxy_set_header Host $host;
    }

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
echo

# ---------- 3. nginx -t ----------
echo "=== 3. nginx -t ==="
if nginx -t 2>&1; then
  echo "[OK] syntax OK"
else
  echo "[!] nginx -t zlyhal. Vrat zalohu:"
  echo "    cp $NGX/nginx.conf.waste.bak $NGX/nginx.conf"
  echo "    rm $NGX/conf.d/waste.conf"
  FAIL=1
fi
echo

# ---------- 4. backup job ----------
echo "=== 4. termux-job-scheduler: backup job ==="
BK="$PWD/scripts/backup/backup-db.sh"
if ! command -v termux-job-scheduler >/dev/null 2>&1; then
  echo "[!] termux-job-scheduler nie je v PATH. Preskakujem."
elif ! [ -x "$BK" ]; then
  echo "[!] $BK nie je spustitelny. chmod +x a spusti znova."
  FAIL=1
else
  if termux-job-scheduler --job-id waste-backup --list 2>/dev/null | grep -q waste-backup; then
    echo "[i] job 'waste-backup' uz existuje."
  else
    termux-job-scheduler --script "$BK" --job-id waste-backup --period-ms 86400000 --network unmetered 2>&1 || {
      echo "[!] registracia zlyhala."
      FAIL=1
    }
    echo "[x] job 'waste-backup' registrovany (kazdych 24h)."
  fi
  echo "[i] Pozn.: termux-job-scheduler je interval, nie cron."
  echo "    Presne 03:00 sa neda. Spusti sa 24h od registracie."
fi
echo

# ---------- 5. dynamicky suhrn ----------
echo "=========================================================="
echo "  SÚHRN (dynamicky)"
echo "=========================================================="
echo "JWT_SECRET:        $([ -f .env ] && grep -qE '^JWT_SECRET=.{32,}' .env && echo OK || echo CHYBA)"
echo "Makefile prod:     $(grep -qE '^prod:' Makefile 2>/dev/null && echo OK || echo CHYBA)"
echo ".gitignore:        $(grep -q '^production_answers.txt$' .gitignore 2>/dev/null && echo OK || echo CHYBA)"
echo "nginx.conf:        $([ -f $NGX/nginx.conf.waste.bak ] && echo 'upraveny (zaloha: .waste.bak)' || echo 'nezmeneny')"
echo "conf.d/waste.conf: $([ -f $NGX/conf.d/waste.conf ] && echo OK || echo CHYBA)"
echo "nginx -t:          $(nginx -t 2>&1 | grep -q 'syntax is ok' && echo OK || echo 'skontroluj manualne')"
echo "backup script:     $([ -x $PWD/scripts/backup/backup-db.sh ] && echo OK || echo CHYBA)"
echo "backup job:        $(termux-job-scheduler --job-id waste-backup --list 2>/dev/null | grep -q waste-backup && echo OK || echo 'neregistrovany')"
echo "cloudflared:       $([ -f ~/.cloudflared/cert.pem ] && echo OK || echo 'neprihlaseny (caka na CF ucet)')"
echo

if [ "$FAIL" = "0" ]; then
  echo "Vsetko, co sa dalo spravit, je spravene."
else
  echo "Nieco zlyhalo. Pozri [!] riadky vyssie."
fi
echo
echo "Dalsie manualne kroky:"
echo "  1) sv up nginx       (ak nginx nebezi)"
echo "  2) curl http://127.0.0.1:8080/health"
echo "  3) sv restart nginx  (po zmene conf.d v buducnosti)"
echo "  4) cloudflared tunel — az ked budes mat CF ucet"
echo
echo "Zmeny v repe:"
git status --short .env Makefile .gitignore 2>/dev/null || true
