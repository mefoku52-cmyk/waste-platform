#!/usr/bin/env bash
set -Eeuo pipefail

DB_URL="${DATABASE_URL:-}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
TG_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TG_CHAT="${TELEGRAM_ADMIN_CHAT_ID:-}"

# Sifrovanie zalohy pred uploadom (age). Kluc NIKDY nie je v repozitari:
# citame iba cestu z prostredia. Bez kluca a recipienta skript nic neposle.
AGE_RECIPIENT="${BACKUP_AGE_RECIPIENT:-}"
AGE_IDENTITY_FILE="${BACKUP_AGE_IDENTITY_FILE:-}"

MIN_SIZE_BYTES=1024
STAMP=$(date +%Y%m%d_%H%M%S)

UPLOAD=0
ENCRYPT=0
for arg in "$@"; do
  case "$arg" in
    --upload) UPLOAD=1; ENCRYPT=1 ;;
    --encrypt) ENCRYPT=1 ;;
  esac
done

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL not set" >&2
  exit 1
fi

DB_URL_PG=$(echo "$DB_URL" | sed 's/+asyncpg//; s/+psycopg2//')
mkdir -p "$BACKUP_DIR"

TMP_DUMP="$BACKUP_DIR/.tmp_${STAMP}.sql"
OUT_GZ="$BACKUP_DIR/waste-platform-${STAMP}.sql.gz"
OUT_AGE="$OUT_GZ.age"
OUT_SHA="$OUT_AGE.sha256"
ERR_LOG="$BACKUP_DIR/.tmp_${STAMP}.err"

echo "[backup] start: $STAMP"
echo "[backup] dir:   $BACKUP_DIR"

if ! pg_dump "$DB_URL_PG" --no-owner --no-privileges --clean --if-exists \
     > "$TMP_DUMP" 2>"$ERR_LOG"; then
  echo "[backup] ERROR: pg_dump failed" >&2
  cat "$ERR_LOG" >&2 || true
  rm -f "$TMP_DUMP" "$ERR_LOG"
  exit 1
fi

TMP_SIZE=$(stat -c%s "$TMP_DUMP" 2>/dev/null || stat -f%z "$TMP_DUMP" 2>/dev/null || echo 0)

if [ "$TMP_SIZE" -lt "$MIN_SIZE_BYTES" ]; then
  echo "[backup] ERROR: dump size $TMP_SIZE B < $MIN_SIZE_BYTES B" >&2
  head -5 "$TMP_DUMP" >&2 || true
  rm -f "$TMP_DUMP" "$ERR_LOG"
  exit 1
fi

if ! gzip -c "$TMP_DUMP" > "$OUT_GZ"; then
  echo "[backup] ERROR: gzip failed" >&2
  rm -f "$TMP_DUMP" "$OUT_GZ" "$ERR_LOG"
  exit 1
fi

if ! gzip -t "$OUT_GZ" 2>/dev/null; then
  echo "[backup] ERROR: gzip integrity check failed" >&2
  rm -f "$TMP_DUMP" "$OUT_GZ" "$ERR_LOG"
  exit 1
fi

GZ_SIZE=$(stat -c%s "$OUT_GZ" 2>/dev/null || stat -f%z "$OUT_GZ" 2>/dev/null || echo 0)
TABLE_COUNT=$(gunzip -c "$OUT_GZ" | grep -c "^CREATE TABLE" || true)
DATA_BLOCKS=$(gunzip -c "$OUT_GZ" | grep -cE "^(INSERT INTO|COPY )" || true)

echo "[backup] OK: $OUT_GZ"
echo "[backup]   size:        ${GZ_SIZE} B (uncompressed: ${TMP_SIZE} B)"
echo "[backup]   tables:      ${TABLE_COUNT}"
echo "[backup]   data blocks: ${DATA_BLOCKS}"

if [ "$TABLE_COUNT" -eq 0 ]; then
  echo "[backup] WARNING: dump contains no tables" >&2
fi

rm -f "$TMP_DUMP" "$ERR_LOG"

# Retencia: 7 dni. Maze aj zasifrovane kopie a ich kontrolne sucty.
find "$BACKUP_DIR" -maxdepth 1 \
  \( -name "waste-platform-*.sql.gz" -o -name "waste-platform-*.sql.gz.age" -o -name "waste-platform-*.sql.gz.age.sha256" \) \
  -type f -mtime +7 -delete 2>/dev/null || true
KEPT=$(ls -1 "$BACKUP_DIR"/waste-platform-*.sql.gz 2>/dev/null | wc -l)
echo "[backup] retention: $KEPT files"

if [ "$ENCRYPT" != "1" ]; then
  echo "[backup] done (no encryption/upload)"
  exit 0
fi

# --- Sifrovanie (a volitelny upload): bez kluca skript zlyha a NIC neposle. ---
if ! command -v age >/dev/null 2>&1; then
  echo "[backup] ERROR: 'age' not installed (encryption requires it)" >&2
  exit 1
fi
if [ -z "$AGE_RECIPIENT" ]; then
  echo "[backup] ERROR: BACKUP_AGE_RECIPIENT not set (encryption requires a recipient key)" >&2
  exit 1
fi
if [ -z "$AGE_IDENTITY_FILE" ] || [ ! -f "$AGE_IDENTITY_FILE" ]; then
  echo "[backup] ERROR: BACKUP_AGE_IDENTITY_FILE missing or not a file (needed to verify decryption)" >&2
  exit 1
fi
if [ "$UPLOAD" = "1" ] && { [ -z "$TG_TOKEN" ] || [ -z "$TG_CHAT" ]; }; then
  echo "[backup] ERROR: TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_CHAT_ID not set" >&2
  exit 1
fi

if ! age --encrypt --recipient "$AGE_RECIPIENT" --output "$OUT_AGE" "$OUT_GZ"; then
  echo "[backup] ERROR: age encryption failed" >&2
  rm -f "$OUT_AGE"
  exit 1
fi

# Kontrolny sucet zasifrovaneho suboru + overenie.
( cd "$BACKUP_DIR" && sha256sum "$(basename "$OUT_AGE")" > "$(basename "$OUT_SHA")" )
if ! ( cd "$BACKUP_DIR" && sha256sum -c "$(basename "$OUT_SHA")" >/dev/null ); then
  echo "[backup] ERROR: checksum verification failed" >&2
  rm -f "$OUT_AGE" "$OUT_SHA"
  exit 1
fi

# Over, ze sa zasifrovany subor da skutocne desifrovat a obsah sedi.
VERIFY_TMP="$BACKUP_DIR/.tmp_${STAMP}.verify.gz"
if ! age --decrypt --identity "$AGE_IDENTITY_FILE" --output "$VERIFY_TMP" "$OUT_AGE" 2>/dev/null; then
  echo "[backup] ERROR: decryption verification failed" >&2
  rm -f "$OUT_AGE" "$OUT_SHA" "$VERIFY_TMP"
  exit 1
fi
if ! cmp -s "$OUT_GZ" "$VERIFY_TMP"; then
  echo "[backup] ERROR: decrypted content does not match source" >&2
  rm -f "$OUT_AGE" "$OUT_SHA" "$VERIFY_TMP"
  exit 1
fi
rm -f "$VERIFY_TMP"

AGE_SIZE=$(stat -c%s "$OUT_AGE" 2>/dev/null || stat -f%z "$OUT_AGE" 2>/dev/null || echo 0)
SHA=$(awk '{print $1}' "$OUT_SHA")
echo "[backup] encrypted: $OUT_AGE (${AGE_SIZE} B)"
echo "[backup] sha256:    $SHA"

if [ "$UPLOAD" != "1" ]; then
  echo "[backup] done (encrypted, no upload)"
  exit 0
fi

echo "[backup] uploading encrypted backup to Telegram..."
CAPTION="DB backup ${STAMP} (age-encrypted) | ${TABLE_COUNT} tables | ${DATA_BLOCKS} data blocks | sha256 ${SHA}"
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
  "https://api.telegram.org/bot${TG_TOKEN}/sendDocument" \
  -F "chat_id=${TG_CHAT}" \
  -F "document=@${OUT_AGE}" \
  -F "caption=${CAPTION}" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "[backup] telegram upload OK"
else
  echo "[backup] WARNING: telegram upload HTTP $HTTP_CODE" >&2
  exit 1
fi

echo "[backup] done"
exit 0
