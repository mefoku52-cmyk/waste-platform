#!/usr/bin/env bash
set -Eeuo pipefail
GROK_SCRIPT="${HOME}/grok.py"
LAYER="${1:-vrstva}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_FILE="vysledok-${LAYER}-${TIMESTAMP}.txt"
if [ ! -f "uloha.txt" ]; then
  echo "[ERROR] uloha.txt neexistuje v aktualnom adresari. Spusti najprv generate_uloha.sh." >&2
  exit 1
fi
if [ ! -f "${GROK_SCRIPT}" ]; then
  echo "[ERROR] grok.py nenajdeny: ${GROK_SCRIPT}" >&2
  exit 1
fi
echo "[INFO] Spustam grok.py nad uloha.txt (vrstva: ${LAYER})..."
python3 "${GROK_SCRIPT}" | tee "${OUTPUT_FILE}"
echo ""
echo "[OK] Vysledok ulozeny do: $(pwd)/${OUTPUT_FILE}"
