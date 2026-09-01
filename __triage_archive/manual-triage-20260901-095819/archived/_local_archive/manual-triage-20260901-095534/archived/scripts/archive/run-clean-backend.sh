#!/data/data/com.termux/files/usr/bin/bash
set -eu

cd "$HOME/waste-platform"
LOG="$HOME/cmep-backend-clean.log"

: > "$LOG"

echo "===== START TIME =====" | tee -a "$LOG"
date -u '+%Y-%m-%dT%H:%M:%SZ' | tee -a "$LOG"

echo "===== SESSION FILE SNAPSHOT =====" | tee -a "$LOG"
nl -ba "$HOME/waste-platform/app/shared/infrastructure/db/session.py" | sed -n '1,120p' | tee -a "$LOG"

echo "===== PYTHON DATABASE_URL CHECK =====" | tee -a "$LOG"
python - <<'PY' | tee -a "$LOG"
from app.shared.infrastructure.db.session import DATABASE_URL
print(DATABASE_URL)
PY

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 >> "$LOG" 2>&1
