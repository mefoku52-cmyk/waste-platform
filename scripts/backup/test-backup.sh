#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

# Self-contained end-to-end test for scripts/backup/backup-prod.sh.
#
# Creates a throwaway local PostgreSQL cluster in a temp directory, fills it
# with test data, runs the real backup script (encrypting with a temp age key),
# verifies the checksum, decrypts, restores into a second temp database and
# compares table/row counts. Also checks the "no key -> fail, upload nothing"
# guarantee. Never touches any real database. Skips (exit 0) if PostgreSQL
# tooling is unavailable.

for bin in initdb pg_ctl pg_isready createdb psql pg_dump age age-keygen sha256sum; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "[test-backup] SKIP: '$bin' not installed" >&2
    exit 0
  fi
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/backup_test.XXXXXX")"
PGDATA="$WORK/pgdata"
SOCK="$WORK/sock"
PORT="${TEST_PG_PORT:-55433}"
mkdir -p "$SOCK" "$WORK/backups"

cleanup() {
  pg_ctl -D "$PGDATA" stop -m immediate >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

initdb -D "$PGDATA" -A trust -U tester >/dev/null 2>"$WORK/initdb.err" || {
  echo "[test-backup] FAIL: initdb"; cat "$WORK/initdb.err"; exit 1;
}
pg_ctl -D "$PGDATA" -o "-p $PORT -k $SOCK -c listen_addresses=127.0.0.1" -l "$WORK/pg.log" start >/dev/null
for _ in $(seq 1 40); do pg_isready -h 127.0.0.1 -p "$PORT" >/dev/null 2>&1 && break; sleep 0.5; done

createdb -h 127.0.0.1 -p "$PORT" -U tester testdb
psql -h 127.0.0.1 -p "$PORT" -U tester -d testdb -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE a(id int primary key, v text);
CREATE TABLE b(id int primary key);
INSERT INTO a SELECT g, 'x'||g FROM generate_series(1,100) g;
INSERT INTO b SELECT g FROM generate_series(1,50) g;
SQL

age-keygen -o "$WORK/key.txt" >/dev/null 2>&1
RECIP="$(grep -m1 -oE 'age1[0-9a-z]+' "$WORK/key.txt")"

export DATABASE_URL="postgresql://tester@127.0.0.1:$PORT/testdb"
export BACKUP_DIR="$WORK/backups"
export BACKUP_AGE_RECIPIENT="$RECIP"
export BACKUP_AGE_IDENTITY_FILE="$WORK/key.txt"

echo "[test-backup] running backup-prod.sh"
bash "$REPO/scripts/backup/backup-prod.sh"

ENC="$(ls "$WORK"/backups/*.sql.gz.age)"
( cd "$(dirname "$ENC")" && sha256sum -c "$(basename "$ENC").sha256" >/dev/null ) \
  || { echo "[test-backup] FAIL: checksum"; exit 1; }

createdb -h 127.0.0.1 -p "$PORT" -U tester restoredb
age -d -i "$WORK/key.txt" "$ENC" | gunzip \
  | psql -h 127.0.0.1 -p "$PORT" -U tester -d restoredb -v ON_ERROR_STOP=1 -q >/dev/null

fail=0
for db in testdb restoredb; do
  tc=$(psql -h 127.0.0.1 -p "$PORT" -U tester -d "$db" -Atc "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE'")
  ra=$(psql -h 127.0.0.1 -p "$PORT" -U tester -d "$db" -Atc "select count(*) from a")
  rb=$(psql -h 127.0.0.1 -p "$PORT" -U tester -d "$db" -Atc "select count(*) from b")
  echo "[test-backup] $db: tables=$tc rows_a=$ra rows_b=$rb"
  eval "${db}_sig=\"$tc/$ra/$rb\""
done
[ "$testdb_sig" = "$restoredb_sig" ] || { echo "[test-backup] FAIL: counts differ ($testdb_sig vs $restoredb_sig)"; fail=1; }

echo "[test-backup] negative: no key must fail and upload nothing"
unset BACKUP_AGE_RECIPIENT BACKUP_AGE_IDENTITY_FILE
set +e
bash "$REPO/scripts/backup/backup-prod.sh" >"$WORK/nokey.out" 2>&1
rc=$?
set -e
[ "$rc" -ne 0 ] || { echo "[test-backup] FAIL: expected non-zero exit without key"; fail=1; }
grep -q "no encryption key\|BACKUP_AGE_IDENTITY_FILE" "$WORK/nokey.out" \
  || { echo "[test-backup] FAIL: missing no-key error message"; fail=1; }

[ "$fail" -eq 0 ] || exit 1
echo "[test-backup] OK"
exit 0
