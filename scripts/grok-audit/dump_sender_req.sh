#!/usr/bin/env bash
set -eu
OUT="${1:-$HOME/waste-platform/scripts/grok-audit/sender_req_diff.txt}"
{
  echo "===== META ====="
  echo "DATE=$(date -Iseconds 2>/dev/null || date)"
  echo "HEAD=$(git rev-parse --short HEAD)"
  echo "BRANCH=$(git rev-parse --abbrev-ref HEAD)"
  echo

  echo "===== STATUS ====="
  git status --short -- app/shared/infrastructure/email/sender.py app/requirements.txt
  echo

  echo "===== DIFF SENDER ====="
  git diff -- app/shared/infrastructure/email/sender.py
  echo

  echo "===== DIFF REQUIREMENTS ====="
  git diff -- app/requirements.txt
  echo

  echo "===== END ====="
} > "$OUT"
echo "WROTE $OUT"
wc -c "$OUT"
