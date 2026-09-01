#!/data/data/com.termux/files/usr/bin/bash
set -eu

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
PGDATA="${PREFIX}/var/lib/postgresql"
PGLOG="${HOME}/postgresql-waste-platform.log"

if [ -f "$PGDATA/PG_VERSION" ]; then
    echo "Cluster already exists: $PGDATA"
    exit 0
fi

mkdir -p "$PGDATA"

initdb \
  -D "$PGDATA" \
  --auth-local=trust \
  --auth-host=scram-sha-256 \
  --username=recyclehub \
  --pwfile=<(printf '%s
' 'recyclehub')

cat >> "$PGDATA/postgresql.conf" <<'CONF'
listen_addresses = '127.0.0.1'
port = 5432
CONF

pg_ctl \
  -D "$PGDATA" \
  -l "$PGLOG" \
  -o "-h 127.0.0.1 -p 5432" \
  start \
  -w

pg_isready -h 127.0.0.1 -p 5432
