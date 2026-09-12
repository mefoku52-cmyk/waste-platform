#!/usr/bin/env bash
set -eu
OUT="${1:-$HOME/waste-platform/scripts/grok-audit/finish_src.txt}"
{
  echo "===== META ====="
  echo "DATE=$(date -Iseconds 2>/dev/null || date)"
  echo "PWD=$(pwd)"
  echo "HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo no-git)"
  echo "BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo no-git)"
  echo

  echo "===== LOCATE ====="
  find app -type f \( -name '*.py' -o -name '*.pyi' \) ! -path '*/__pycache__/*' \
    | sort
  echo
  echo "--- hits ---"
  grep -RIn --include='*.py' -E 'forgot-password|forgot_password|Redis is not reachable|password reset|def health|/health' app \
    | grep -v __pycache__ || true
  echo

  dump() {
    echo "===== FILE $1 ====="
    if [ -f "$1" ]; then
      echo "BYTES=$(wc -c < "$1" | tr -d ' ')"
      echo "-----BEGIN-----"
      cat "$1"
      echo
      echo "-----END-----"
    else
      echo "ABSENT $1"
    fi
    echo
  }

  dump app/core/config.py
  dump app/main.py

  echo "===== CANDIDATE FILES FROM HITS ====="
  grep -RIl --include='*.py' -E 'forgot-password|forgot_password|Redis is not reachable|password reset' app \
    | grep -v __pycache__ | sort -u | while read -r f; do
      dump "$f"
    done

  echo "===== HEALTH FILES ====="
  grep -RIl --include='*.py' -E 'def health|/health|database_url' app \
    | grep -v __pycache__ | sort -u | while read -r f; do
      dump "$f"
    done

  echo "===== EMAIL SENDER ====="
  dump app/shared/infrastructure/email/sender.py

  echo "===== END ====="
} > "$OUT"
echo "WROTE $OUT"
wc -c "$OUT"
