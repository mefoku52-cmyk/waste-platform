#!/data/data/com.termux/files/usr/bin/bash
set -eu

echo '===== TIME ====='
date -u '+%Y-%m-%dT%H:%M:%SZ'
echo

echo '===== PSQL VERSION ====='
psql --version || true
echo

echo '===== PG ISREADY ====='
pg_isready -h 127.0.0.1 -p 5432 -d recyclehub -U recyclehub || true
echo

echo '===== TCP PROBE VIA BASH ====='
python - <<'PY'
import socket
s = socket.socket()
s.settimeout(3)
try:
    s.connect(("127.0.0.1", 5432))
    print("TCP_CONNECT=OK")
except Exception as e:
    print("TCP_CONNECT=FAIL", repr(e))
finally:
    s.close()
PY
echo

echo '===== PSQL DIRECT CONNECT ====='
PGPASSWORD=recyclehub psql -h 127.0.0.1 -p 5432 -U recyclehub -d recyclehub -c 'select version();' || true
echo

echo '===== PSQL DATABASE LIST ====='
PGPASSWORD=recyclehub psql -h 127.0.0.1 -p 5432 -U recyclehub -d recyclehub -c 'l' || true
