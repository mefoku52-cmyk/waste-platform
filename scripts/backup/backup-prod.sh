#!/usr/bin/env bash
set -Eeuo pipefail

DB_URL="${DATABASE_URL:-}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
TG_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TG_CHAT="${TELEGRAM_ADMIN_CHAT_ID:-}"
MIN_SIZE_BYTES=1024
STAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL not set" >&2
  exit 1
fi

DB_URL_PG=$(echo "$DB_URL" | sed 's/+asyncpg//; s/+psycopg2//')
mkdir -p "$BACKUP_DIR"

TMP_DUMP="$BACKUP_DIR/.tmp_${STAMP}.sql"
OUT_GZ="$BACKUP_DIR/waste-platform-${STAMP}.sql.gz"
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

find "$BACKUP_DIR" -name "waste-platform-*.sql.gz" -type f -mtime +7 -delete 2>/dev/null || true
KEPT=$(ls -1 "$BACKUP_DIR"/waste-platform-*.sql.gz 2>/dev/null | wc -l)
echo "[backup] retention: $KEPT files"

if [ "${1:-}" = "--upload" ] && [ -n "$TG_TOKEN" ] && [ -n "$TG_CHAT" ]; then
  echo "[backup] uploading to Telegram..."
  CAPTION="DB backup ${STAMP} | ${GZ_SIZE} B | ${TABLE_COUNT} tables | ${DATA_BLOCKS} data blocks"
  HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
    "https://api.telegram.org/bot${TG_TOKEN}/sendDocument" \
    -F "chat_id=${TG_CHAT}" \
    -F "document=@${OUT_GZ}" \
    -F "caption=${CAPTION}" 2>&1)

  if [ "$HTTP_CODE" = "200" ]; then
    echo "[backup] telegram upload OK"
  else
    echo "[backup] WARNING: telegram upload HTTP $HTTP_CODE" >&2
  fi
fi

echo "[backup] done"
exit 0
