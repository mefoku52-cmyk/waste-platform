#!/usr/bin/env bash
set -Eeuo pipefail

# Kontrola poslednej zalohy: vek, velkost, integrita.
# Podporuje nezasifrovane (.sql.gz) aj zasifrovane (.sql.gz.age + .sha256).

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/waste-platform}"
MIN_SIZE=1024
MAX_AGE_HOURS=26

if [ ! -d "$BACKUP_DIR" ]; then
  echo "[health] FAIL: $BACKUP_DIR not found" >&2
  exit 2
fi

shopt -s nullglob
CANDIDATES=("$BACKUP_DIR"/waste-platform-*.sql.gz "$BACKUP_DIR"/waste-platform-*.sql.gz.age)
shopt -u nullglob

LATEST=""
for f in "${CANDIDATES[@]}"; do
  [ -f "$f" ] || continue
  if [ -z "$LATEST" ] || [ "$f" -nt "$LATEST" ]; then
    LATEST="$f"
  fi
done

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

case "$LATEST" in
  *.age)
    SHA_FILE="${LATEST}.sha256"
    if [ ! -f "$SHA_FILE" ]; then
      echo "[health] FAIL: checksum file missing for encrypted backup" >&2
      FAIL=1
    elif ! ( cd "$BACKUP_DIR" && sha256sum -c "$(basename "$SHA_FILE")" >/dev/null 2>&1 ); then
      echo "[health] FAIL: checksum mismatch" >&2
      FAIL=1
    else
      echo "[health] checksum OK"
    fi
    ;;
  *)
    gzip -t "$LATEST" 2>/dev/null || { echo "[health] FAIL: gzip" >&2; FAIL=1; }
    ;;
esac

[ "$FAIL" -eq 1 ] && exit 1
echo "[health] OK"
exit 0
