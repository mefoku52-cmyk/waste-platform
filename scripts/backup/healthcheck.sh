#!/usr/bin/env bash
set -Eeuo pipefail

# Validate the latest encrypted backup: age, size, and checksum.
# Backups produced by backup-prod.sh are age-encrypted (suffix .sql.gz.age)
# with a sibling .sha256 checksum file.

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
MIN_SIZE=1024
MAX_AGE_HOURS=26

if [ ! -d "$BACKUP_DIR" ]; then
  echo "[health] FAIL: $BACKUP_DIR not found" >&2
  exit 2
fi

LATEST=$(ls -1t "$BACKUP_DIR"/waste-platform-*.sql.gz.age 2>/dev/null | head -1)

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

# checksum verification (if the sidecar exists)
if [ -f "${LATEST}.sha256" ]; then
  if ( cd "$(dirname "$LATEST")" && sha256sum -c "$(basename "$LATEST").sha256" >/dev/null 2>&1 ); then
    echo "[health] checksum: OK"
  else
    echo "[health] FAIL: checksum mismatch" >&2
    FAIL=1
  fi
else
  echo "[health] WARNING: no checksum sidecar" >&2
fi

# decryptability check (only when an identity file is configured)
if [ -n "${BACKUP_AGE_IDENTITY_FILE:-}" ] && [ -r "${BACKUP_AGE_IDENTITY_FILE}" ]; then
  if age -d -i "${BACKUP_AGE_IDENTITY_FILE}" "$LATEST" 2>/dev/null | gzip -t 2>/dev/null; then
    echo "[health] decrypt: OK"
  else
    echo "[health] FAIL: cannot decrypt/verify backup" >&2
    FAIL=1
  fi
else
  echo "[health] decrypt: SKIPPED (BACKUP_AGE_IDENTITY_FILE not set)"
fi

[ "$FAIL" -eq 1 ] && exit 1
echo "[health] OK"
exit 0
