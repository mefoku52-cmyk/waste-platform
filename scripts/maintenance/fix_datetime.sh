#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

FILES=(
  app/modules/auth/domain/entities.py
  app/shared/domain/base.py
  app/shared/application/side_effects.py
  app/modules/auth/infrastructure/repositories.py
  app/modules/listings/application/services.py
  app/modules/inquiries/application/services.py
  app/modules/inquiries/presentation/router.py
  app/modules/analytics/domain/entities.py
)

for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "[i] chýba: $f"
    continue
  fi

  # 1) doplň UTC do importu, ak tam nie je
  if grep -qE '^from datetime import ' "$f"; then
    if ! grep -qE '^from datetime import .*\bUTC\b' "$f"; then
      sed -i -E 's/^from datetime import (.*)$/from datetime import UTC, \1/' "$f"
      echo "[x] UTC import pridaný: $f"
    fi
  else
    echo "[!] žiadny 'from datetime import' v $f — skontroluj manuálne"
  fi

  # 2) nahraď datetime.now() a datetime.utcnow() za datetime.now(UTC)
  sed -i 's/datetime\.now()/datetime.now(UTC)/g' "$f"
  sed -i 's/datetime\.utcnow()/datetime.now(UTC)/g' "$f"
done

echo
echo "=== Kontrola ==="
for f in "${FILES[@]}"; do
  echo "--- $f ---"
  grep -n "from datetime\|datetime\.now\|datetime\.utcnow" "$f" || true
done

echo
echo "=== pytest na jednom teste ==="
pytest tests/unit/test_refresh_session_entity.py -q
