#!/usr/bin/env bash
set -eu
OUT="${1:-$HOME/waste-platform/scripts/grok-audit/inventory_noise.txt}"
{
  echo "===== META ====="
  echo "DATE=$(date -Iseconds 2>/dev/null || date)"
  echo "HEAD=$(git rev-parse --short HEAD)"
  echo "BRANCH=$(git rev-parse --abbrev-ref HEAD)"
  echo

  echo "===== TRACKED LARGE FILES ====="
  git ls-files -z | xargs -0 ls -l 2>/dev/null | awk '$5+0 > 500000 {print $5, $9}' | sort -nr | head -n 40
  echo

  echo "===== TRACKED NOISE CANDIDATES ====="
  git ls-files \
    | grep -E '^(archived-phase-scripts/|audit-output/|_quarantine/|\.closure_truth|P0_|p0_03_|R60_|R_REQUIREMENT|GLOBAL_P0|audit_final|audit_master|VPS_LOCAL)' \
    | head -n 200
  echo "TRACKED_NOISE_COUNT=$(git ls-files | grep -cE '^(archived-phase-scripts/|audit-output/|_quarantine/|\.closure_truth|P0_|p0_03_|R60_|audit_final|audit_master)' || true)"
  echo

  echo "===== UNTRACKED ====="
  git status -u --short | head -n 80
  echo

  echo "===== DIRS SIZES ====="
  du -sh archived-phase-scripts audit-output _quarantine scripts/grok-audit .production-release audit 2>/dev/null || true
  echo

  echo "===== KEEP ====="
  for f in app/core/config.py app/main.py app/modules/auth/application/password_reset.py \
           app/shared/infrastructure/email/sender.py app/requirements.txt \
           docker-compose.yml .github/workflows/release.yml .github/workflows/ci.yml
  do
    if [ -e "$f" ]; then echo "KEEP $f"; fi
  done
  echo
  echo "===== END ====="
} > "$OUT"
echo "WROTE $OUT"
wc -c "$OUT"
