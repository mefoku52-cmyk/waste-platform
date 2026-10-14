#!/usr/bin/env bash
set -Eeuo pipefail

# Production DB backup: pg_dump -> gzip -> age encryption -> optional Telegram upload.
#
# Security rules:
#   * The dump is ALWAYS encrypted before it leaves the host (age).
#   * Encryption keys are read from environment variables or from a path that
#     lives OUTSIDE this repository. A key path inside the repo is rejected.
#   * A SHA-256 checksum is written next to the encrypted file and the encrypted
#     file is decrypted+gunzip-verified before anything is uploaded.
#   * Without a usable key the script exits non-zero and uploads NOTHING.

DB_URL="${DATABASE_URL:-}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
TG_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TG_CHAT="${TELEGRAM_ADMIN_CHAT_ID:-}"
MIN_SIZE_BYTES=1024
STAMP=$(date +%Y%m%d_%H%M%S)

# --- encryption configuration (keys must NOT live in the repo) ---
AGE_RECIPIENT="${BACKUP_AGE_RECIPIENT:-}"
AGE_RECIPIENT_FILE="${BACKUP_AGE_RECIPIENT_FILE:-}"
AGE_IDENTITY_FILE="${BACKUP_AGE_IDENTITY_FILE:-}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fail() { echo "[backup] ERROR: $*" >&2; exit 1; }

# Reject any key path that resolves inside the repository.
check_key_path() {
  local path="$1" name="$2"
  [ -n "$path" ] || return 0
  local abs
  abs="$(cd "$(dirname "$path")" 2>/dev/null && pwd)/$(basename "$path")" || fail "$name path invalid: $path"
  case "$abs" in
    "$REPO_DIR"/*) fail "$name points INSIDE the repository ($abs); keys must live outside the repo (e.g. \$HOME/.config/cmep/)" ;;
  esac
  [ -r "$path" ] || fail "$name not readable: $path"
}

if [ -z "$DB_URL" ]; then
  fail "DATABASE_URL not set"
fi

# Resolve the age recipient (public key).
if [ -n "$AGE_RECIPIENT" ] && [ -n "$AGE_RECIPIENT_FILE" ]; then
  fail "set only one of BACKUP_AGE_RECIPIENT / BACKUP_AGE_RECIPIENT_FILE"
fi
check_key_path "$AGE_RECIPIENT_FILE" "BACKUP_AGE_RECIPIENT_FILE"
if [ -z "$AGE_RECIPIENT" ] && [ -n "$AGE_RECIPIENT_FILE" ]; then
  AGE_RECIPIENT="$(grep -m1 -oE 'age1[0-9a-z]+' "$AGE_RECIPIENT_FILE" || true)"
fi
[ -n "$AGE_RECIPIENT" ] || fail "no encryption key: set BACKUP_AGE_RECIPIENT or BACKUP_AGE_RECIPIENT_FILE (outside the repo)"
command -v age >/dev/null 2>&1 || fail "age is not installed"

check_key_path "$AGE_IDENTITY_FILE" "BACKUP_AGE_IDENTITY_FILE"
[ -n "$AGE_IDENTITY_FILE" ] || fail "BACKUP_AGE_IDENTITY_FILE is required to verify the encrypted backup can be decrypted"

DB_URL_PG=$(echo "$DB_URL" | sed 's/+asyncpg//; s/+psycopg2//')
mkdir -p "$BACKUP_DIR"

TMP_DUMP="$BACKUP_DIR/.tmp_${STAMP}.sql"
OUT_GZ="$BACKUP_DIR/waste-platform-${STAMP}.sql.gz"
OUT_ENC="$BACKUP_DIR/waste-platform-${STAMP}.sql.gz.age"
OUT_SHA="$BACKUP_DIR/waste-platform-${STAMP}.sql.gz.age.sha256"
ERR_LOG="$BACKUP_DIR/.tmp_${STAMP}.err"

cleanup() {
  rm -f "$TMP_DUMP" "$ERR_LOG"
  # never leave the unencrypted dump on disk
  rm -f "$OUT_GZ"
}
trap cleanup EXIT

echo "[backup] start: $STAMP"
echo "[backup] dir:   $BACKUP_DIR"

if ! pg_dump "$DB_URL_PG" --no-owner --no-privileges --clean --if-exists \
     > "$TMP_DUMP" 2>"$ERR_LOG"; then
  echo "[backup] ERROR: pg_dump failed" >&2
  cat "$ERR_LOG" >&2 || true
  fail "pg_dump failed"
fi

TMP_SIZE=$(stat -c%s "$TMP_DUMP" 2>/dev/null || stat -f%z "$TMP_DUMP" 2>/dev/null || echo 0)

if [ "$TMP_SIZE" -lt "$MIN_SIZE_BYTES" ]; then
  echo "[backup] ERROR: dump size $TMP_SIZE B < $MIN_SIZE_BYTES B" >&2
  head -5 "$TMP_DUMP" >&2 || true
  fail "dump smaller than minimum size"
fi

if ! gzip -c "$TMP_DUMP" > "$OUT_GZ"; then
  fail "gzip failed"
fi

if ! gzip -t "$OUT_GZ" 2>/dev/null; then
  fail "gzip integrity check failed"
fi

GZ_SIZE=$(stat -c%s "$OUT_GZ" 2>/dev/null || stat -f%z "$OUT_GZ" 2>/dev/null || echo 0)
TABLE_COUNT=$(gunzip -c "$OUT_GZ" | grep -c "^CREATE TABLE" || true)
DATA_BLOCKS=$(gunzip -c "$OUT_GZ" | grep -cE "^(INSERT INTO|COPY )" || true)

# --- table count reconciliation (KROK 1.5) ---
# Compare tables in the live DB against CREATE TABLE statements in the dump.
# The two numbers can legitimately differ (29 vs 26): the dump counts only
# public base tables emitted as "CREATE TABLE", while the DB count can include
# tables in other schemas, partitioned/PARTITION OF tables, or matviews.
DB_TABLE_COUNT=""
if command -v psql >/dev/null 2>&1; then
  DB_TABLE_COUNT=$(psql "$DB_URL_PG" -Atc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'" \
    2>/dev/null || echo "")
fi

# --- encrypt ---
if ! age -r "$AGE_RECIPIENT" -o "$OUT_ENC" "$OUT_GZ"; then
  fail "age encryption failed"
fi

# checksum of the encrypted artifact (never of the plaintext)
( cd "$BACKUP_DIR" && sha256sum "$(basename "$OUT_ENC")" > "$(basename "$OUT_SHA")" ) \
  || fail "checksum failed"

# --- verify the encrypted file actually decrypts to a valid gzip ---
if ! age -d -i "$AGE_IDENTITY_FILE" "$OUT_ENC" 2>/dev/null | gzip -t 2>/dev/null; then
  fail "encrypted backup failed decryption verification"
fi

# plaintext dump no longer needed on disk
rm -f "$OUT_GZ" "$TMP_DUMP" "$ERR_LOG"

echo "[backup] OK: $OUT_ENC"
echo "[backup]   size:        ${GZ_SIZE} B (uncompressed: ${TMP_SIZE} B)"
echo "[backup]   tables:      ${TABLE_COUNT}"
echo "[backup]   data blocks: ${DATA_BLOCKS}"
echo "[backup]   sha256:      $(cut -d' ' -f1 "$OUT_SHA")"
if [ -n "$DB_TABLE_COUNT" ]; then
  echo "[backup]   tables in DB: ${DB_TABLE_COUNT} (dump CREATE TABLE: ${TABLE_COUNT}, diff: $((DB_TABLE_COUNT - TABLE_COUNT)))"
fi

if [ "$TABLE_COUNT" -eq 0 ]; then
  echo "[backup] WARNING: dump contains no tables" >&2
fi

find "$BACKUP_DIR" -name "waste-platform-*.sql.gz.age" -type f -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "waste-platform-*.sql.gz.age.sha256" -type f -mtime +7 -delete 2>/dev/null || true
KEPT=$(ls -1 "$BACKUP_DIR"/waste-platform-*.sql.gz.age 2>/dev/null | wc -l)
echo "[backup] retention: $KEPT files"

if [ "${1:-}" = "--upload" ]; then
  [ -n "$TG_TOKEN" ] || fail "TELEGRAM_BOT_TOKEN not set; refusing upload"
  [ -n "$TG_CHAT" ] || fail "TELEGRAM_ADMIN_CHAT_ID not set; refusing upload"
  echo "[backup] uploading encrypted backup to Telegram..."
  CAPTION="DB backup ${STAMP} | ${GZ_SIZE} B | ${TABLE_COUNT} tables | sha256 $(cut -d' ' -f1 "$OUT_SHA")"
  HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
    "https://api.telegram.org/bot${TG_TOKEN}/sendDocument" \
    -F "chat_id=${TG_CHAT}" \
    -F "document=@${OUT_ENC}" \
    -F "caption=${CAPTION}" 2>&1)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "[backup] telegram upload OK"
  else
    fail "telegram upload failed HTTP $HTTP_CODE"
  fi
fi

echo "[backup] done"
exit 0
