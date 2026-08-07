#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEADER_FILE="${SCRIPT_DIR}/grok_prompt_header.txt"
OUTPUT_FILE="uloha.txt"
if [ "$#" -eq 0 ]; then
  echo "[ERROR] Zadaj aspon jeden subor na analyzu." >&2
  exit 1
fi
if [ ! -f "${HEADER_FILE}" ]; then
  echo "[ERROR] Chyba hlavicka promptu: ${HEADER_FILE}" >&2
  exit 1
fi
cp "${HEADER_FILE}" "${OUTPUT_FILE}"
for f in "$@"; do
  if [ ! -f "${f}" ]; then
    echo "[ERROR] Subor neexistuje, preskakujem: ${f}" >&2
    continue
  fi
  {
    echo ""
    echo "===SUBOR: ${f}==="
    cat "${f}"
  } >> "${OUTPUT_FILE}"
done
LINES=$(wc -l < "${OUTPUT_FILE}")
echo "[OK] Vygenerovany ${OUTPUT_FILE} (${LINES} riadkov)"
