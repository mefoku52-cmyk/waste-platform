#!/usr/bin/env bash
set -Eeuo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
MIN_SIZE=1024
MAX_AGE_HOURS=26

if [ ! -d "$BACKUP_DIR" ]; then
  echo "[health] FAIL: $BACKUP_DIR not found" >&2
  exit 2
fi

LATEST=$(ls -1t "$BACKUP_DIR"/waste-platform-*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
  echo "[health] FAIL: no backup found" >&2
  exit 2
fi

AGE_SECONDS=$(( $(date +%s) - $(stat -c%Y "$LATEST" 2>/dev/null || stat -f%m "$LATEST" 2>/dev/null || echo 0) ))
AGE_HOURS=$(( AGE_SECONDS / 3600 ))
SIZE=$(stat -c%s "$LATEST" 2>/dev/null || stat -f%z "$LATEST" 2>/dev/null || echo 0)

echo "[health] latest: $LATEST"
echo "[health] age:    ${AGE_HOURS}h (max ${MAX_AGE_HOURS}h)"
echo "[health] size:   ${SIZE} B (min ${MIN_SIZE} B)"

FAIL=0
[ "$SIZE" -lt "$MIN_SIZE" ] && { echo "[health] FAIL: size" >&2; FAIL=1; }
[ "$AGE_HOURS" -gt "$MAX_AGE_HOURS" ] && { echo "[health] FAIL: age" >&2; FAIL=1; }
gzip -t "$LATEST" 2>/dev/null || { echo "[health] FAIL: gzip" >&2; FAIL=1; }

[ "$FAIL" -eq 1 ] && exit 1
echo "[health] OK"
exit 0
