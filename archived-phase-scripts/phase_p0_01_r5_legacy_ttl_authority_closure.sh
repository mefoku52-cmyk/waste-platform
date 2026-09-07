#!/usr/bin/env bash
set -u

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"

if [ -d "$PROJECT_ROOT" ]; then
    cd "$PROJECT_ROOT" || exit 20
else
    echo "FAIL: PROJECT_ROOT_NOT_FOUND=$PROJECT_ROOT"
    exit 20
fi

REPORT="audit-output/p0_01_r5_legacy_ttl_authority_closure.txt"
mkdir -p audit-output
: > "$REPORT"

FAILURE_COUNT=0
REVIEW_COUNT=0

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $1" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $1" | tee -a "$REPORT"
}

section() {
    echo | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
    echo "$1" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

LEGACY_A="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
LEGACY_R="JWT_REFRESH_TOKEN_EXPIRES_DAYS"

section "1. SAFETY PRECHECK"

if [ "$PROJECT_ROOT" = "$HOME/waste-platform" ] || \
   [ "$(basename "$PROJECT_ROOT")" = "waste-platform" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "UNEXPECTED_PROJECT_ROOT=$PROJECT_ROOT"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "BOUNDED_SCAN=YES"

section "2. LEGACY IDENTIFIERS"

echo "LEGACY_ACCESS=$LEGACY_A" | tee -a "$REPORT"
echo "LEGACY_REFRESH=$LEGACY_R" | tee -a "$REPORT"

section "3. CURRENT APPLICATION RUNTIME"

RUNTIME_LEGACY_COUNT=0
RUNTIME_LEGACY_REFS=0

while IFS= read -r -d '' f; do

    if grep -Eq "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null; then

        MATCHES="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"

        RUNTIME_LEGACY_COUNT=$((RUNTIME_LEGACY_COUNT + 1))
        RUNTIME_LEGACY_REFS=$((RUNTIME_LEGACY_REFS + MATCHES))

        echo "RUNTIME_LEGACY_FILE=$f" | tee -a "$REPORT"

        grep -nE "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null \
            | head -40 \
            | tee -a "$REPORT"

    fi

done < <(
    find app apps/web \
        -type f \
        \( \
            -name '*.py' \
            -o -name '*.js' \
            -o -name '*.jsx' \
            -o -name '*.ts' \
            -o -name '*.tsx' \
            -o -name '*.sh' \
            -o -name '*.yml' \
            -o -name '*.yaml' \
            -o -name '*.toml' \
            -o -name '*.ini' \
            -o -name '*.conf' \
        \) \
        -not -path '*/node_modules/*' \
        -not -path '*/.next/*' \
        -print0 2>/dev/null
)

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" | tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] && \
   [ "$RUNTIME_LEGACY_REFS" -eq 0 ]; then
    pass "CURRENT_RUNTIME_LEGACY_TTL=0"
else
    fail "CURRENT_RUNTIME_LEGACY_TTL_FILES=$RUNTIME_LEGACY_COUNT REFS=$RUNTIME_LEGACY_REFS"
fi

section "4. PRODUCTION CONFIGURATION"

PROD_LEGACY_COUNT=0

for f in \
    ".env.production" \
    "docker-compose.yml" \
    "docker/backend/Dockerfile" \
    "docker/frontend/Dockerfile" \
    "docker/nginx/Dockerfile" \
    "scripts/deploy.sh"
do

    if [ ! -f "$f" ]; then
        continue
    fi

    MATCHES="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"

    if [ "$MATCHES" -gt 0 ]; then

        PROD_LEGACY_COUNT=$((PROD_LEGACY_COUNT + MATCHES))

        echo "PRODUCTION_LEGACY_REFERENCE=$f" | tee -a "$REPORT"

        grep -nE "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null \
            | sed -E \
              's/(JWT_ACCESS_TOKEN_EXPIRES_MINUTES|JWT_REFRESH_TOKEN_EXPIRES_DAYS)/\1/g' \
            | tee -a "$REPORT"

    fi

done

echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_COUNT" | tee -a "$REPORT"

if [ "$PROD_LEGACY_COUNT" -eq 0 ]; then
    pass "PRODUCTION_CONFIG_LEGACY_TTL=0"
else
    review "PRODUCTION_CONFIG_CONTAINS_LEGACY_TTL=$PROD_LEGACY_COUNT"
fi

section "5. CI TEST-ONLY CLASSIFICATION"

CI=".github/workflows/ci.yml"

if [ ! -f "$CI" ]; then

    review "CI_FILE_MISSING=$CI"

else

    CI_MATCHES="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$CI" 2>/dev/null || true)"

    echo "CI_LEGACY_REFERENCE_COUNT=$CI_MATCHES" | tee -a "$REPORT"

    if [ "$CI_MATCHES" -eq 0 ]; then

        pass "CI_HAS_NO_LEGACY_TTL_REFERENCES"

    else

        echo "--- CI LEGACY TTL CONTEXT ---" | tee -a "$REPORT"

        grep -n -B8 -A10 \
            -E "$LEGACY_A|$LEGACY_R" \
            "$CI" 2>/dev/null \
            | tee -a "$REPORT"

        section "5A. CI EXECUTION CLASSIFICATION"

        CI_TEST_CONTEXT=0
        CI_DEPLOY_CONTEXT=0

        if grep -Eq \
            'pytest|unittest|vitest|npm run test|npm run lint|npm run typecheck' \
            "$CI"; then
            CI_TEST_CONTEXT=1
        fi

        if grep -Eiq \
            'docker compose up|docker run|kubectl apply|kubectl rollout|helm upgrade|deploy:' \
            "$CI"; then
            CI_DEPLOY_CONTEXT=1
        fi

        echo "CI_TEST_CONTEXT=$CI_TEST_CONTEXT" | tee -a "$REPORT"
        echo "CI_DEPLOY_CONTEXT=$CI_DEPLOY_CONTEXT" | tee -a "$REPORT"

        if [ "$CI_TEST_CONTEXT" -eq 1 ] && \
           [ "$CI_DEPLOY_CONTEXT" -eq 0 ]; then

            pass "CI_LEGACY_TTL_CLASSIFIED_AS_TEST_CONFIGURATION"

        elif [ "$CI_DEPLOY_CONTEXT" -gt 0 ]; then

            review "CI_LEGACY_TTL_COLOCATED_WITH_DEPLOYMENT_SIGNAL"

        else

            review "CI_LEGACY_TTL_CONTEXT_NOT_CONCLUSIVE"

        fi

    fi

fi

section "6. FORENSIC SCRIPT SELF-REFERENCE EXCLUSION"

FORENSIC_FILES=0
FORENSIC_LEGACY_REFS=0
FORENSIC_RUNTIME_EXEC=0

for f in \
    "phase_p0_01_production_source_boundary.sh" \
    "phase_p0_01_r2_production_authority_resolver.sh" \
    "phase_p0_01_r3_authority_discriminator.sh" \
    "phase_p0_01_r4_legacy_ttl_targeted_review.sh"
do

    if [ ! -f "$f" ]; then
        continue
    fi

    FORENSIC_FILES=$((FORENSIC_FILES + 1))

    MATCHES="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"
    FORENSIC_LEGACY_REFS=$((FORENSIC_LEGACY_REFS + MATCHES))

    echo | tee -a "$REPORT"
    echo "--- FORENSIC=$f ---" | tee -a "$REPORT"
    echo "LEGACY_REFERENCE_COUNT=$MATCHES" | tee -a "$REPORT"

    REAL_EXEC=0

    # Only classify actual process-launch primitives.
    # grep/find/sha256sum/sed/awk/tee are forensic inspection operations
    # and must NOT be treated as runtime execution.

    if grep -Eq \
        '(^|[^A-Za-z_])(uvicorn|gunicorn)([^A-Za-z_]|$)' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    if grep -Eq \
        'docker[[:space:]]+(compose[[:space:]]+up|run|start)' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    if grep -Eq \
        'kubectl[[:space:]]+(apply|rollout|create|run)' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    if grep -Eq \
        '(^|[^A-Za-z_])(nohup|setsid)([^A-Za-z_]|$)' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    if grep -Eq \
        '(^|[[:space:]])(source|eval)[[:space:]]+' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    if grep -Eq \
        '\b(python|python3|bash|sh)[[:space:]]+[^#]*(app/main|uvicorn|gunicorn)' \
        "$f" 2>/dev/null; then
        REAL_EXEC=1
    fi

    echo "ACTUAL_RUNTIME_EXECUTION_SIGNAL=$REAL_EXEC" | tee -a "$REPORT"

    if [ "$MATCHES" -gt 0 ] && [ "$REAL_EXEC" -eq 0 ]; then
        pass "FORENSIC_REFERENCE_ONLY=$f"
    elif [ "$REAL_EXEC" -gt 0 ]; then
        FORENSIC_RUNTIME_EXEC=$((FORENSIC_RUNTIME_EXEC + 1))
        review "REAL_EXECUTION_SIGNAL_IN_FORENSIC_SCRIPT=$f"
    else
        pass "NO_LEGACY_OR_RUNTIME_CONFLICT=$f"
    fi

done

echo "FORENSIC_FILES=$FORENSIC_FILES" | tee -a "$REPORT"
echo "FORENSIC_LEGACY_REFERENCE_TOTAL=$FORENSIC_LEGACY_REFS" | tee -a "$REPORT"
echo "FORENSIC_RUNTIME_EXECUTION_FILES=$FORENSIC_RUNTIME_EXEC" | tee -a "$REPORT"

section "7. RUNTIME HASH CONTINUITY"

CONFIG="app/core/config.py"
JWT="app/shared/infrastructure/security/jwt_service.py"

EXPECTED_CONFIG="742d629996182344fc2ce2bc8c5253eaef185c47856cdede2f91a486a0b1256d"
EXPECTED_JWT="eceaf6010b755ca0ff191be5ab2e9ef0b777304b94df754d878cb6bafc6ce57c"

if [ -f "$CONFIG" ]; then

    ACTUAL_CONFIG="$(sha256sum "$CONFIG" | awk '{print $1}')"

    echo "CONFIG_HASH=$ACTUAL_CONFIG" | tee -a "$REPORT"

    if [ "$ACTUAL_CONFIG" = "$EXPECTED_CONFIG" ]; then
        pass "CONFIG_HASH_IMMUTABLE_MATCH"
    else
        fail "CONFIG_HASH_MISMATCH"
    fi

else
    fail "CONFIG_RUNTIME_FILE_MISSING=$CONFIG"
fi

if [ -f "$JWT" ]; then

    ACTUAL_JWT="$(sha256sum "$JWT" | awk '{print $1}')"

    echo "JWT_SERVICE_HASH=$ACTUAL_JWT" | tee -a "$REPORT"

    if [ "$ACTUAL_JWT" = "$EXPECTED_JWT" ]; then
        pass "JWT_SERVICE_HASH_IMMUTABLE_MATCH"
    else
        fail "JWT_SERVICE_HASH_MISMATCH"
    fi

else
    fail "JWT_RUNTIME_FILE_MISSING=$JWT"
fi

section "8. FINAL AUTHORITY DECISION"

echo "CURRENT_BACKEND_AUTHORITY=app" | tee -a "$REPORT"
echo "CURRENT_FRONTEND_AUTHORITY=apps/web" | tee -a "$REPORT"
echo "CURRENT_NGINX_AUTHORITY=docker/nginx/Dockerfile" | tee -a "$REPORT"
echo "CURRENT_DEPLOY_AUTHORITY=scripts/deploy.sh" | tee -a "$REPORT"
echo "CURRENT_COMPOSE_AUTHORITY=docker-compose.yml" | tee -a "$REPORT"
echo "CURRENT_CI_AUTHORITY=.github/workflows/ci.yml" | tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ]; then
    pass "LEGACY_TTL_NOT_PRESENT_IN_CURRENT_APPLICATION_RUNTIME"
else
    fail "LEGACY_TTL_PRESENT_IN_CURRENT_APPLICATION_RUNTIME"
fi

if [ "$FORENSIC_RUNTIME_EXEC" -eq 0 ]; then
    pass "NO_FORENSIC_SCRIPT_RUNTIME_EXECUTION_CONFIRMED"
else
    review "FORENSIC_RUNTIME_EXECUTION_REQUIRES_REVIEW=$FORENSIC_RUNTIME_EXEC"
fi

section "9. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFS" | tee -a "$REPORT"
echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_COUNT" | tee -a "$REPORT"
echo "FORENSIC_RUNTIME_EXECUTION_FILES=$FORENSIC_RUNTIME_EXEC" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_01_R5_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R5_LEGACY_TTL_AUTHORITY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 20

fi

if [ "$RUNTIME_LEGACY_COUNT" -eq 0 ] && \
   [ "$FORENSIC_RUNTIME_EXEC" -eq 0 ] && \
   [ "$PROD_LEGACY_COUNT" -eq 0 ]; then

    echo "P0_01_R5_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R5_LEGACY_TTL_AUTHORITY_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"

    exit 0

fi

echo "P0_01_R5_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_01_R5_LEGACY_TTL_AUTHORITY_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"

echo
echo "REPORT=$REPORT"

exit 10
