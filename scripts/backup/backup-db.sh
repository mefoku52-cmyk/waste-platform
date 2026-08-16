#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="${HOME}/cmep-backups"
mkdir -p "$OUT_DIR"
DB="${POSTGRES_DB:-cmep}"
USER="${POSTGRES_USER:-u0_a388}"
FILE="\( {OUT_DIR}/cmep-pg- \){STAMP}.sql.gz"
pg_dump -U "$USER" -d "$DB" | gzip > "$FILE"
echo "OK \( {FILE} ( \)(du -h "$FILE" | cut -f1))"
ls -1t "$OUT_DIR"/cmep-pg-*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
