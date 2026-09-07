#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/waste-platform"
cd "$ROOT" || exit 1

echo "============================================================"
echo "R60 EXACT FAILURE EVIDENCE"
echo "============================================================"
echo "DATE=$(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJECT=$ROOT"
echo "MODE=READ_ONLY"
echo "============================================================"

TEST="$ROOT/.production-release/r60-test/test-r60-release-aware-deploy.sh"

echo
echo "============================================================"
echo "1. R60 TEST SOURCE"
echo "============================================================"

if [ ! -f "$TEST" ]; then
    echo "R60_TEST_FILE=NOT_FOUND"
    exit 1
fi

echo "FILE=${TEST#$ROOT/}"
echo

nl -ba "$TEST" | sed -n '1,230p'

echo
echo "============================================================"
echo "2. ALL FAILURE PRODUCING ASSERTIONS"
echo "============================================================"

grep -nE \
    'fail "[^"]+"|FAIL:|FAILURES=|R60_TEST_STATUS=FAIL|exit [^0]' \
    "$TEST" 2>/dev/null || true

echo
echo "============================================================"
echo "3. ALL TEST CASE LABELS"
echo "============================================================"

grep -nE \
    'pass "[^"]+"|fail "[^"]+"' \
    "$TEST" 2>/dev/null || true

echo
echo "============================================================"
echo "4. R60 RESULT BLOCK"
echo "============================================================"

nl -ba "$TEST" | sed -n '185,215p'

echo
echo "============================================================"
echo "5. HISTORICAL R60 EXECUTION EVIDENCE"
echo "============================================================"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    ! -path '*/__pycache__/*' \
    ! -name 'inspect_r60_exact_failure.sh' \
    ! -name 'R60_R65_FORENSIC_RECONCILIATION_*.txt' \
    -print 2>/dev/null |
while IFS= read -r f; do
    grep -HnEi \
        'R60_TEST_STATUS|R60 TEST RESULT|FAILURES=[1-9]|FAIL:|test-r60-release-aware-deploy' \
        "$f" 2>/dev/null || true
done |
head -200

echo
echo "============================================================"
echo "6. R60 DEPLOY/COMPOSE CONDITIONS REFERENCED BY TEST"
echo "============================================================"

echo "--- deploy.sh / compose references ---"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    '(REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|COMPOSE_ENV_FILE_AUTHORITY_PRESERVED|VALID_RELEASE_ID_ACCEPTED|VALID_IMAGE_TAG_ACCEPTED|MUTABLE_IDENTITY_REJECTED|DEPLOY_DOES_NOT_CONTAIN_SECRET_VALUES)' \
    "$ROOT/.production-release/r60-test" \
    "$ROOT/.production-release/r61-backup-" \
    "$ROOT/docker-compose.yml" \
    "$ROOT/scripts/deploy.sh" \
    2>/dev/null || true

echo
echo "============================================================"
echo "7. R60 FAILURE CLASSIFICATION"
echo "============================================================"

FAIL_LINES="$(
    grep -nE \
        'fail "[^"]+"' \
        "$TEST" 2>/dev/null || true
)"

if [ -z "$FAIL_LINES" ]; then
    echo "STATIC_FAIL_BRANCHES=NONE"
else
    echo "$FAIL_LINES"
fi

echo
echo "============================================================"
echo "8. AUTHORITY RULE"
echo "============================================================"

echo "R60_TEST_STATUS=FAIL is evidence that at least one assertion"
echo "failed during an execution, but this inspection does NOT"
echo "invent which assertion failed."
echo
echo "A concrete R60 blocker requires either:"
echo "  A) historical execution output containing FAIL:<label>"
echo "  B) a reproducible current test failure with its exact label"
echo "  C) another authoritative artifact identifying the failed assertion"
echo
echo "NO_REMEDIATION=YES"
echo "NO_R66=YES"
echo "NO_PROJECT_MODIFICATION=YES"
echo "============================================================"
