#!/usr/bin/env bash
set -uo pipefail
cd ~/waste-platform

echo "==============================================="
echo " 1. Nájdi __init__.py, ktoré importujú zmazaný .router / .schemas"
echo "==============================================="
grep -R --exclude-dir=__pycache__ -n "from \.router import\|from \.schemas import\|from \. import router\|from \. import schemas" \
  app/modules/*/__init__.py 2>/dev/null || true

echo
echo "==============================================="
echo " 2. Prepíš __init__.py na presentation vrstvu"
echo "==============================================="
for m in admin analytics compliance documents inquiries notifications; do
  f="app/modules/$m/__init__.py"
  if [ -f "$f" ]; then
    if grep -q "from \.router import" "$f" 2>/dev/null; then
      # nahraď top-level import za presentation import
      sed -i 's|^from \.router import router$|from .presentation.router import router|' "$f"
      echo "[x] upravené: $f"
    else
      echo "[i] bez zmeny: $f"
    fi
  fi
done

echo
echo "==============================================="
echo " 3. Over, či niekde zostal odkaz na zmazaný .router / .schemas"
echo "==============================================="
grep -R --exclude-dir=__pycache__ -n "modules\.\(admin\|analytics\|compliance\|documents\|inquiries\|notifications\)\.router\b" \
  app tests docs 2>/dev/null || echo "[ok] žiadne odkazy na top-level .router"
grep -R --exclude-dir=__pycache__ -n "modules\.\(admin\|analytics\|compliance\|documents\|inquiries\|notifications\)\.schemas\b" \
  app tests docs 2>/dev/null || echo "[ok] žiadne odkazy na top-level .schemas"

echo
echo "==============================================="
echo " 4. Over obsah __init__.py po zmene"
echo "==============================================="
for m in admin analytics compliance documents inquiries notifications; do
  echo "--- app/modules/$m/__init__.py ---"
  cat "app/modules/$m/__init__.py" 2>/dev/null || echo "[i] neexistuje"
done

echo
echo "==============================================="
echo " 5. Rýchly import test"
echo "==============================================="
python -c "import app.shared.infrastructure.db.register_models; print('[ok] register_models import prešiel')" \
  || echo "[!] import stále padá, pozri traceback vyššie"

echo
echo "==============================================="
echo " 6. Spusti pytest"
echo "==============================================="
pytest
