#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/prioritize_domains_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== PRIORITIZE DOMAINS ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

cat <<'TABLE'
DOMAIN | BACKEND | FRONTEND | APP_TESTS | ROOT_TESTS | SCORE | CLASS
auth | YES | YES | YES | YES | 4 | strong_e2e
companies | YES | YES | YES | YES | 4 | strong_e2e
listings | YES | YES | YES | YES | 4 | strong_e2e
users | YES | NO | YES | NO | 2 | backend_strong_front_missing
inquiries | YES | YES | YES | NO | 3 | nearly_e2e
documents | YES | YES | YES | NO | 3 | nearly_e2e
uploads | YES | YES | YES | NO | 3 | nearly_e2e
compliance | YES | YES | NO | NO | 2 | ui_backend_no_tests
notifications | YES | YES | NO | NO | 2 | ui_backend_no_tests
admin | YES | YES | NO | NO | 2 | ui_backend_no_tests
company_memberships | YES | NO | NO | NO | 1 | backend_only
analytics | YES | NO | NO | NO | 1 | backend_only
TABLE

echo
echo "=== PRIORITY ORDER ==="
echo "P1: compliance, notifications, admin"
echo "P2: inquiries, documents, uploads"
echo "P3: users"
echo "P4: company_memberships, analytics"
echo "P5: repo hygiene / root audit artifacts"
echo
echo "REPORT: $REPORT"
echo "=== KONIEC PRIORITIZE DOMAINS ==="
