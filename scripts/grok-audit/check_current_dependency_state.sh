#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
APP="$PROJECT/app"

echo "=== AKTUALNY ADRESAR ==="
pwd

echo
echo "=== EXISTENCIA KLUCOVYCH SUBOROV ==="
for f in \
  "$APP/Dockerfile" \
  "$APP/requirements.txt" \
  "$APP/pyproject.toml" \
  "$PROJECT/requirements.txt" \
  "$PROJECT/pyproject.toml"
do
  if [ -f "$f" ]; then
    echo "[EXISTUJE] $f"
  else
    echo "[CHYBA]    $f"
  fi
done

echo
echo "=== APP/DOCKERFILE: RIADKY SUVISIACE SO ZAVISLOSTAMI ==="
if [ -f "$APP/Dockerfile" ]; then
  nl -ba "$APP/Dockerfile" | grep -E 'requirements|pip install|uvicorn|^' || true
else
  echo "[CHYBA] Dockerfile neexistuje: $APP/Dockerfile"
fi

echo
echo "=== OBSAH APP/REQUIREMENTS.TXT, AK EXISTUJE ==="
if [ -f "$APP/requirements.txt" ]; then
  nl -ba "$APP/requirements.txt"
else
  echo "[INFO] app/requirements.txt momentalne neexistuje"
fi

echo
echo "=== PYTHON A NAINSTALOVANE KLUCOVE BALIKY ==="
python3 -c 'import sys; print("PYTHON:", sys.executable); print("PREFIX:", sys.prefix)'
for package in fastapi PyJWT python-jose passlib prometheus-client pydantic SQLAlchemy uvicorn; do
  if python3 -m pip show "$package" >/dev/null 2>&1; then
    python3 -m pip show "$package" | grep -E '^(Name|Version):'
  else
    echo "[NENAINSTALOVANY] $package"
  fi
done

echo
echo "=== KONIEC DIAGNOSTIKY ==="
