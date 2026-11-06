#!/usr/bin/env bash
set -Eeuo pipefail

# End-to-end test zalohy: docasne lokalne PostgreSQL clustery -> pg_dump ->
# gzip -> age sifrovanie -> desifrovanie -> obnova -> porovnanie poctov.
# NEPRIPAjA sa k ziadnej existujucej databaze. Vsetko v docasnom adresari.
# Pouzitie: bash scripts/backup/backup-restore-test.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_SCRIPT="${REPO_ROOT}/scripts/backup/backup-prod.sh"
PORT_SRC=55441
PORT_DST=55442

WORK="$(mktemp -d "${TMPDIR:-/tmp}/bkp_test.XXXXXX")"
SOCK_SRC="$WORK/sock1"
SOCK_DST="$WORK/sock2"
DATA_SRC="$WORK/data1"
DATA_DST="$WORK/data2"
BACKUP_DIR="$WORK/backups"
DUMP_DB="t_src"
DST_DB="t_dst"
FAIL=0

cleanup() {
  pg_ctl -D "$DATA_SRC" stop >/dev/null 2>&1 || true
  pg_ctl -D "$DATA_DST" stop >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

say() { printf '%s\n' "$*"; }
check() { if [ "$2" = "$3" ]; then say "PASS: $1 ($2)"; else say "FAIL: $1 expected=$3 got=$2"; FAIL=1; fi; }

require() { command -v "$1" >/dev/null 2>&1 || { say "FAIL: missing tool $1"; exit 2; }; }
for t in initdb pg_ctl psql pg_dump gzip age age-keygen sha256sum gunzip; do require "$t"; done
[ -x "$BACKUP_SCRIPT" ] || [ -f "$BACKUP_SCRIPT" ] || { say "FAIL: backup script not found"; exit 2; }

say "work dir: $WORK"
mkdir -p "$SOCK_SRC" "$SOCK_DST" "$BACKUP_DIR"

# --- age kluce (mimo repozitara, v docasnom adresari) ---
age-keygen -o "$WORK/age.key" 2>"$WORK/age.pub"
AGE_RECIPIENT="$(grep -oE 'age1[0-9a-z]+' "$WORK/age.pub" | head -1)"
[ -n "$AGE_RECIPIENT" ] || { say "FAIL: could not read age recipient"; exit 2; }
say "age recipient: $AGE_RECIPIENT"

# --- clustery ---
initdb -D "$DATA_SRC" -A trust -U postgres --no-locale -E UTF8 >"$WORK/initdb_src.log" 2>&1
initdb -D "$DATA_DST" -A trust -U postgres --no-locale -E UTF8 >"$WORK/initdb_dst.log" 2>&1
pg_ctl -D "$DATA_SRC" -o "-p $PORT_SRC -k $SOCK_SRC -c listen_addresses=''" -l "$WORK/pg_src.log" start >/dev/null 2>&1
pg_ctl -D "$DATA_DST" -o "-p $PORT_DST -k $SOCK_DST -c listen_addresses=''" -l "$WORK/pg_dst.log" start >/dev/null 2>&1
say "clusters started (src:$PORT_SRC dst:$PORT_DST)"

psql -h "$SOCK_SRC" -p "$PORT_SRC" -U postgres -q -c "create database $DUMP_DB;" >/dev/null
psql -h "$SOCK_DST" -p "$PORT_DST" -U postgres -q -c "create database $DST_DB;" >/dev/null

# --- seed ---
psql -h "$SOCK_SRC" -p "$PORT_SRC" -U postgres -d "$DUMP_DB" -q <<'SQL'
create table companies (id serial primary key, name text not null);
create table listings (id serial primary key, company_id int references companies(id), title text);
create table notes (id serial primary key, body text);
insert into companies (name) select 'Firma ' || g from generate_series(1, 25) g;
insert into listings (company_id, title) select (g % 25) + 1, 'Ponuka ' || g from generate_series(1, 80) g;
insert into notes (body) select 'poznamka ' || g from generate_series(1, 5) g;
SQL
say "seed done"

# --- spusti realny backup skript (sifrovany) ---
DATABASE_URL="postgresql://postgres@/$DUMP_DB?host=$SOCK_SRC&port=$PORT_SRC" \
BACKUP_DIR="$BACKUP_DIR" \
BACKUP_AGE_RECIPIENT="$AGE_RECIPIENT" \
BACKUP_AGE_IDENTITY_FILE="$WORK/age.key" \
  bash "$BACKUP_SCRIPT" --encrypt >"$WORK/backup.out" 2>&1 || { say "FAIL: backup script returned non-zero"; cat "$WORK/backup.out"; exit 1; }
say "--- backup output ---"; cat "$WORK/backup.out"

OUT_GZ="$(ls -1 "$BACKUP_DIR"/waste-platform-*.sql.gz 2>/dev/null | head -1)"
OUT_AGE="$OUT_GZ.age"
OUT_SHA="$OUT_AGE.sha256"
[ -f "$OUT_GZ" ] && say "PASS: plaintext gz exists" || { say "FAIL: no .gz"; FAIL=1; }
[ -f "$OUT_AGE" ] && say "PASS: encrypted .age exists" || { say "FAIL: no .age"; FAIL=1; }
[ -f "$OUT_SHA" ] && say "PASS: checksum file exists" || { say "FAIL: no .sha256"; FAIL=1; }

# --- kontrolny sucet ---
( cd "$BACKUP_DIR" && sha256sum -c "$(basename "$OUT_SHA")" >"$WORK/sha.out" 2>&1 )
grep -q ': OK' "$WORK/sha.out" && say "PASS: sha256 verification" || { say "FAIL: sha256 verification"; cat "$WORK/sha.out"; FAIL=1; }

# --- desifrovanie ---
age --decrypt --identity "$WORK/age.key" --output "$WORK/dec.gz" "$OUT_AGE" 2>"$WORK/age_dec.err" \
  && say "PASS: decryption succeeded" || { say "FAIL: decryption"; cat "$WORK/age_dec.err"; FAIL=1; }
cmp -s "$OUT_GZ" "$WORK/dec.gz" && say "PASS: decrypted == original gz" || { say "FAIL: decrypted differs"; FAIL=1; }

# --- obnova do druhej DB ---
gunzip -c "$WORK/dec.gz" | psql -h "$SOCK_DST" -p "$PORT_DST" -U postgres -d "$DST_DB" -q >"$WORK/restore.out" 2>&1 \
  && say "PASS: restore succeeded" || { say "FAIL: restore"; cat "$WORK/restore.out"; FAIL=1; }

# --- porovnanie ---
table_count() { psql -h "$1" -p "$2" -U postgres -d "$3" -tAc \
  "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE'"; }
total_rows() {
  local sock=$1 port=$2 db=$3 total=0 t c
  for t in $(psql -h "$sock" -p "$port" -U postgres -d "$db" -tAc \
      "select tablename from pg_tables where schemaname='public' order by 1"); do
    c=$(psql -h "$sock" -p "$port" -U postgres -d "$db" -tAc "select count(*) from \"$t\"")
    total=$((total + c))
  done
  echo "$total"
}

SRC_T=$(table_count "$SOCK_SRC" "$PORT_SRC" "$DUMP_DB")
DST_T=$(table_count "$SOCK_DST" "$PORT_DST" "$DST_DB")
SRC_R=$(total_rows "$SOCK_SRC" "$PORT_SRC" "$DUMP_DB")
DST_R=$(total_rows "$SOCK_DST" "$PORT_DST" "$DST_DB")
say "src tables=$SRC_T rows=$SRC_R | dst tables=$DST_T rows=$DST_R"
check "table count match" "$DST_T" "$SRC_T"
check "row count match" "$DST_R" "$SRC_R"

# --- negativny test: zly DB -> ziadny subor ---
BAD_DIR="$WORK/bad_backups"; mkdir -p "$BAD_DIR"
if DATABASE_URL="postgresql://postgres@/nonexistent_db?host=$SOCK_SRC&port=$PORT_SRC" \
   BACKUP_DIR="$BAD_DIR" bash "$BACKUP_SCRIPT" >"$WORK/bad.out" 2>&1; then
  say "FAIL: backup against bad DB returned success"; FAIL=1
else
  say "PASS: backup against bad DB failed as expected"
fi
if ls "$BAD_DIR"/waste-platform-*.sql.gz >/dev/null 2>&1; then
  say "FAIL: bad backup left a .gz file"; FAIL=1
else
  say "PASS: bad backup left no .gz file"
fi

if [ "$FAIL" -eq 0 ]; then say "=== RESULT: ALL PASS ==="; else say "=== RESULT: FAILURES PRESENT ==="; fi
exit "$FAIL"
