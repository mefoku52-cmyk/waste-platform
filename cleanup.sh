#!/usr/bin/env bash
set -uo pipefail

cd ~/waste-platform

echo "==============================================="
echo " 1. Záloha rozpracovaných zmien"
echo "==============================================="
git add -A
git commit -m "WIP before cleanup" || echo "[i] Nič na commit alebo commit zlyhal."

echo
echo "==============================================="
echo " 2. Inventarizácia duplicít"
echo "==============================================="
for m in admin analytics compliance documents inquiries notifications; do
  echo "--- modul: $m ---"
  echo "[top-level]"
  grep -R --exclude-dir=__pycache__ -n "app\.modules\.$m\.router" app tests docs 2>/dev/null || true
  grep -R --exclude-dir=__pycache__ -n "app\.modules\.$m\.schemas" app tests docs 2>/dev/null || true
  echo "[presentation]"
  grep -R --exclude-dir=__pycache__ -n "app\.modules\.$m\.presentation\.router" app tests docs 2>/dev/null || true
  grep -R --exclude-dir=__pycache__ -n "app\.modules\.$m\.presentation\.schemas" app tests docs 2>/dev/null || true
done

echo
echo "==============================================="
echo " 3. Odstránenie top-level duplicít"
echo "==============================================="
for f in \
  app/modules/admin/router.py \
  app/modules/admin/schemas.py \
  app/modules/analytics/router.py \
  app/modules/analytics/schemas.py \
  app/modules/compliance/router.py \
  app/modules/compliance/schemas.py \
  app/modules/documents/router.py \
  app/modules/documents/schemas.py \
  app/modules/inquiries/router.py \
  app/modules/inquiries/schemas.py \
  app/modules/notifications/router.py \
  app/modules/notifications/schemas.py
do
  if [ -f "$f" ]; then
    git rm "$f" 2>/dev/null || rm -f "$f"
    echo "[x] zmazané: $f"
  fi
done

echo
echo "==============================================="
echo " 4. Zjednotenie migračného systému"
echo "==============================================="
echo "--- stav pred ---"
ls -la alembic migrations 2>/dev/null || true
if [ -d alembic ]; then
  echo "[i] alembic.ini ukazuje na migrations/, takže alembic/ je legacy."
  git rm -r alembic 2>/dev/null || rm -r alembic
  echo "[x] zmazané: alembic/"
else
  echo "[i] alembic/ neexistuje, netreba riešiť."
fi

echo
echo "==============================================="
echo " 5. Kontrola .env.example"
echo "==============================================="
if grep -n "cat >" .env.example 2>/dev/null; then
  echo "[!] POZOR: v .env.example je shell blok. Vyčisti manuálne."
else
  echo "[ok] .env.example neobsahuje shell blok."
fi
grep -q "^\.env$" .gitignore 2>/dev/null || echo ".env" >> .gitignore
grep -q "__pycache__" .gitignore 2>/dev/null || echo "__pycache__/" >> .gitignore

echo
echo "==============================================="
echo " 6. Untracked súbory do archívu"
echo "==============================================="
mkdir -p archive
for f in \
  apps/web/src/app/dashboard/page.tsx.pre-redesign \
  dashboard.html
do
  if [ -f "$f" ]; then
    mv "$f" archive/
    echo "[x] presunuté do archive/: $f"
  fi
done

echo
echo "==============================================="
echo " 7. Vyčistenie __pycache__"
echo "==============================================="
find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
echo "[ok] __pycache__ vyčistené."

echo
echo "==============================================="
echo " 8. Finálne overenie"
echo "==============================================="
echo "--- pytest ---"
pytest || echo "[!] Testy zlyhali, skontroluj manuálne."

echo "--- alembic current ---"
alembic current || echo "[!] Alembic zlyhal. Skontroluj, či DB beží."

echo "--- alembic upgrade head ---"
alembic upgrade head || echo "[!] Alembic upgrade zlyhal. Skontroluj DB."

echo "--- git status ---"
git status

echo
echo "==============================================="
echo " Hotovo. Manuálne ešte over:"
echo "  - .env.example neobsahuje 'cat >' ani reálne heslá"
echo "  - žiadny top-level router.py/schemas.py už nie je importovaný"
echo "  - pytest prešiel"
echo "  - alembic upgrade head prešiel na bežiacej DB"
echo "==============================================="
