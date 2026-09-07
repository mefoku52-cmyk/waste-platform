#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/waste-platform"
cd "$ROOT" || exit 1

TEST="$ROOT/.production-release/r60-test/test-r60-release-aware-deploy.sh"
DEPLOY="$ROOT/scripts/deploy.sh"
COMPOSE="$ROOT/docker-compose.yml"
R61="$ROOT/.production-release/r61-backup-20260903_104708"

echo "============================================================"
echo "R60 FIVE FAILURES -> R61 FORENSIC RECONCILIATION"
echo "============================================================"
echo "DATE=$(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJECT=$ROOT"
echo "MODE=READ_ONLY"
echo "============================================================"

echo
echo "============================================================"
echo "1. EXACT R60 ASSERTION IMPLEMENTATIONS"
echo "============================================================"

for label in \
    API_EXPLICIT_RELEASE_IMAGE \
    WEB_EXPLICIT_RELEASE_IMAGE \
    COMPOSE_CONFIG_VALIDATION_PRESENT \
    EXPLICIT_API_WEB_BUILD_PRESENT \
    COMPOSE_ENV_FILE_AUTHORITY_PRESERVED
do
    echo
    echo "--- $label ---"
    grep -n -B8 -A12 "$label" "$TEST" 2>/dev/null || true
done

echo
echo "============================================================"
echo "2. CURRENT docker-compose.yml RELEVANT EVIDENCE"
echo "============================================================"

if [ -f "$COMPOSE" ]; then
    nl -ba "$COMPOSE" | sed -n '1,180p'
else
    echo "COMPOSE=NOT_FOUND"
fi

echo
echo "============================================================"
echo "3. CURRENT deploy.sh RELEVANT EVIDENCE"
echo "============================================================"

if [ -f "$DEPLOY" ]; then
    nl -ba "$DEPLOY" | sed -n '1,180p'
else
    echo "DEPLOY=NOT_FOUND"
fi

echo
echo "============================================================"
echo "4. R61 ARTIFACT INVENTORY"
echo "============================================================"

if [ -d "$R61" ]; then
    find "$R61" -maxdepth 2 -type f -print | sort
else
    echo "R61=NOT_FOUND"
fi

echo
echo "============================================================"
echo "5. R61 deploy.sh"
echo "============================================================"

if [ -f "$R61/deploy.sh" ]; then
    nl -ba "$R61/deploy.sh" | sed -n '1,220p'
else
    echo "R61_DEPLOY=NOT_FOUND"
fi

echo
echo "============================================================"
echo "6. R61 docker-compose.yml"
echo "============================================================"

if [ -f "$R61/docker-compose.yml" ]; then
    nl -ba "$R61/docker-compose.yml" | sed -n '1,180p'
else
    echo "R61_COMPOSE=NOT_FOUND"
fi

echo
echo "============================================================"
echo "7. DIRECT STRUCTURAL COMPARISON: CURRENT vs R61"
echo "============================================================"

if [ -f "$R61/docker-compose.yml" ] && [ -f "$COMPOSE" ]; then
    echo "--- docker-compose diff ---"
    diff -u "$R61/docker-compose.yml" "$COMPOSE" || true
else
    echo "COMPOSE_COMPARISON=UNAVAILABLE"
fi

if [ -f "$R61/deploy.sh" ] && [ -f "$DEPLOY" ]; then
    echo
    echo "--- deploy.sh diff ---"
    diff -u "$R61/deploy.sh" "$DEPLOY" || true
else
    echo "DEPLOY_COMPARISON=UNAVAILABLE"
fi

echo
echo "============================================================"
echo "8. R61 REFERENCES TO THE FIVE R60 FAILURE DOMAINS"
echo "============================================================"

if [ -d "$R61" ]; then
    grep -RInE \
        --exclude-dir=.git \
        '(explicit.*release|release.*image|image:|docker compose config|compose config|config.*valid|build:|env_file|ENV_FILE|environment:|REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|up --build|--build)' \
        "$R61" 2>/dev/null || true
else
    echo "R61_REFERENCE_SCAN=NOT_FOUND"
fi

echo
echo "============================================================"
echo "9. CURRENT REPOSITORY REFERENCES TO R60 FAILURE LABELS"
echo "============================================================"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    '(API_EXPLICIT_RELEASE_IMAGE|WEB_EXPLICIT_RELEASE_IMAGE|COMPOSE_CONFIG_VALIDATION_PRESENT|EXPLICIT_API_WEB_BUILD_PRESENT|COMPOSE_ENV_FILE_AUTHORITY_PRESERVED)' \
    "$ROOT" 2>/dev/null |
grep -v 'inspect_r60_failures_vs_r61.sh' |
head -300 || true

echo
echo "============================================================"
echo "10. R61 TEMPORAL / REMEDIATION LANGUAGE"
echo "============================================================"

grep -RInEi \
    --exclude-dir=.git \
    '(R60|remediat|fix|repair|correct|address|blocker|failure|release-aware|release aware|production release)' \
    "$R61" 2>/dev/null |
head -300 || true

echo
echo "============================================================"
echo "11. AUTHORITY CHECK"
echo "============================================================"

echo "R60_CURRENT_REPRODUCED=YES"
echo "R60_FAILURE_COUNT=5"
echo "R60_FAILURES=API_EXPLICIT_RELEASE_IMAGE,WEB_EXPLICIT_RELEASE_IMAGE,COMPOSE_CONFIG_VALIDATION_PRESENT,EXPLICIT_API_WEB_BUILD_PRESENT,COMPOSE_ENV_FILE_AUTHORITY_PRESERVED"
echo
echo "R61_PHYSICAL_ARTIFACTS_PRESENT=$( [ -d "$R61" ] && echo YES || echo NO )"
echo
echo "IMPORTANT:"
echo "Temporal adjacency R60 -> R61 is NOT treated as remediation evidence."
echo "A remediation claim requires structural correspondence plus evidence."
echo
echo "NO_REMEDIATION=YES"
echo "NO_R66=YES"
echo "NO_PROJECT_MODIFICATION=YES"
echo "============================================================"
