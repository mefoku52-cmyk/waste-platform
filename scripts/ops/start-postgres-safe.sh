#!/data/data/com.termux/files/usr/bin/bash
set -u

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
PGDATA="${PREFIX}/var/lib/postgresql"
PGLOG="${HOME}/postgresql-waste-platform.log"

echo '===== TIME ====='
date -u '+%Y-%m-%dT%H:%M:%SZ'
echo

echo '===== POSTGRES BINARIES ====='
command -v postgres || true
command -v pg_ctl || true
command -v initdb || true
command -v pg_isready || true
echo

echo '===== PGDATA ====='
echo "PGDATA=$PGDATA"
if [ -d "$PGDATA" ]; then
    ls -ld "$PGDATA"
    find "$PGDATA" -maxdepth 1 -mindepth 1 -printf '%f
' 2>/dev/null | sort || true
else
    echo "PGDATA_MISSING"
fi
echo

echo '===== EXISTING SERVER STATUS ====='
pg_ctl -D "$PGDATA" status 2>&1 || true
echo

if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo '===== NO INITIALIZED CLUSTER ====='
    echo 'PG_VERSION_MISSING'
    echo 'ACTION_REQUIRED=initdb'
    exit 2
fi

echo '===== STARTING EXISTING CLUSTER ====='
pg_ctl -D "$PGDATA" -l "$PGLOG" -o "-h 127.0.0.1 -p 5432" start -w 2>&1 || true
echo

echo '===== SERVER STATUS AFTER START ====='
pg_ctl -D "$PGDATA" status 2>&1 || true
echo

echo '===== READINESS ====='
pg_isready -h 127.0.0.1 -p 5432 || true
echo

echo '===== POSTGRES LOG ====='
tail -n 100 "$PGLOG" 2>/dev/null || true
