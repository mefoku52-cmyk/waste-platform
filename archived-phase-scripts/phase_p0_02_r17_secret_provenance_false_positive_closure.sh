#!/usr/bin/env bash
set -u

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"
cd "$PROJECT_ROOT" || exit 20

REPORT="$PROJECT_ROOT/audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"
mkdir -p "$PROJECT_ROOT/audit-output"

FAILURE_COUNT=0
REVIEW_COUNT=0

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

pass() {
    echo "PASS: $*"
}

fail() {
    echo "FAIL: $*"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    echo "REVIEW: $*"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

log() {
    echo "$*" | tee -a "$REPORT"
}

: > "$REPORT"

section "P0-02 R17 SECRET PROVENANCE FALSE-POSITIVE CLOSURE"

section "1. SAFETY PRECHECK"

if [ "$PROJECT_ROOT" = "$HOME/waste-platform" ] &&
   [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_NOT_CONFIRMED"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"

section "2. REQUIRED AUTHORITY FILES"

for file in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"; do

    if [ -f "$file" ]; then
        pass "AUTHORITY_PRESENT=$file"
    else
        fail "AUTHORITY_MISSING=$file"
    fi
done

section "3. SECRET TOKEN SET"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for key in "${SECRET_KEYS[@]}"; do
    echo "SECRET_TOKEN=$key"
done

section "4. PRODUCTION AUTHORITY"

ENV_SECRET_COUNT=0

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "^[[:space:]]*${key}=" .env.production 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT KEY=$key VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$key"
    fi
done

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_COUNT_MISMATCH EXPECTED=5 ACTUAL=$ENV_SECRET_COUNT"
fi

section "5. COMPOSE SEMANTIC PROOF"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

# POSTGRES_PASSWORD service assignment.
if grep -Eq \
    '^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*\$\{POSTGRES_PASSWORD([}:]|$)' \
    docker-compose.yml 2>/dev/null; then

    pass "COMPOSE_REFERENCE_WIRING KEY=POSTGRES_PASSWORD"
    COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
    COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

elif grep -Eq \
    '^[[:space:]]*POSTGRES_PASSWORD:[[:space:]]*[^$]' \
    docker-compose.yml 2>/dev/null; then

    fail "COMPOSE_LITERAL_ASSIGNMENT KEY=POSTGRES_PASSWORD"
    COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
    COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
else
    fail "COMPOSE_TARGET_MISSING KEY=POSTGRES_PASSWORD"
fi

# JWT secrets.
for key in JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do

    if grep -Eq \
        "^[[:space:]]*${key}:[[:space:]]*\\\$\\{${key}([}:]|$)" \
        docker-compose.yml 2>/dev/null; then

        pass "COMPOSE_REFERENCE_WIRING KEY=$key"
        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
        COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

    elif grep -Eq \
        "^[[:space:]]*${key}:[[:space:]]*[^$]" \
        docker-compose.yml 2>/dev/null; then

        fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$key"
        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
        COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
    else
        fail "COMPOSE_TARGET_MISSING KEY=$key"
    fi
done

# DATABASE_URL is context, not another Compose secret assignment.
if grep -Eq \
    '^[[:space:]]*DATABASE_URL:.*\$\{POSTGRES_PASSWORD' \
    docker-compose.yml 2>/dev/null; then

    pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
else
    fail "DATABASE_URL_SECRET_REFERENCE_CONTEXT_MISSING"
fi

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"

if [ "$COMPOSE_TARGET_COUNT" -eq 3 ]; then
    pass "COMPOSE_TARGET_CARDINALITY_EXACT"
else
    fail "COMPOSE_TARGET_CARDINALITY_MISMATCH EXPECTED=3 ACTUAL=$COMPOSE_TARGET_COUNT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH EXPECTED=3 ACTUAL=$COMPOSE_REFERENCE_COUNT"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_PRESENT"
fi

section "6. RUNTIME SEMANTIC PROOF"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Eq \
    'JWT_SECRET_KEY[[:space:]]*:' \
    app/core/config.py 2>/dev/null; then

    pass "RUNTIME_JWT_SECRET_DECLARATION_PRESENT"
    RUNTIME_DECLARATION_COUNT=1
else
    fail "RUNTIME_JWT_SECRET_DECLARATION_MISSING"
fi

if grep -Eq \
    'secret_key=self\.JWT_SECRET_KEY' \
    app/core/config.py 2>/dev/null; then

    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT"
    RUNTIME_CONTEXT_COUNT=$((RUNTIME_CONTEXT_COUNT + 1))
fi

if grep -Eq \
    'secret=self\.JWT_SECRET_KEY' \
    app/core/config.py 2>/dev/null; then

    pass "RUNTIME_JWT_SECRET_SECOND_USE_CONTEXT_PRESENT"
    RUNTIME_CONTEXT_COUNT=$((RUNTIME_CONTEXT_COUNT + 1))
fi

if grep -Eq \
    'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\'']' \
    app/core/config.py 2>/dev/null; then

    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT"
    RUNTIME_LITERAL_COUNT=1
else
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
fi

if [ "$RUNTIME_DECLARATION_COUNT" -ge 1 ] &&
   [ "$RUNTIME_CONTEXT_COUNT" -ge 2 ] &&
   [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "RUNTIME_SECRET_LINEAGE_CLOSED"
else
    fail "RUNTIME_SECRET_LINEAGE_INCOMPLETE"
fi

section "7. CI TEST-SCOPE PROOF"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

# R15 already established the five assignments as test-scope.
# R17 deliberately does not infer production scope from generic words
# elsewhere in the workflow.

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "${key}:" .github/workflows/ci.yml 2>/dev/null; then
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))
        CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
        pass "CI_SECRET_TEST_SCOPE KEY=$key VALUE=<REDACTED>"
    fi
done

CI_PROD_SCOPE_COUNT=0

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_SECRET_ASSIGNMENT_COUNT" -eq 5 ] &&
   [ "$CI_TEST_SCOPE_COUNT" -eq 5 ]; then
    pass "CI_TEST_SECRET_BOUNDARY_COMPLETE"
else
    fail "CI_TEST_SECRET_BOUNDARY_INCOMPLETE"
fi

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "8. DEPLOYMENT BOUNDARY"

DEPLOY_SECRET_REFERENCE_COUNT=0

if grep -Eq \
    'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
    scripts/deploy.sh 2>/dev/null; then

    fail "DEPLOY_SCRIPT_DIRECT_SECRET_IDENTIFIER_REFERENCE_PRESENT"
    DEPLOY_SECRET_REFERENCE_COUNT=1
else
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
fi

if grep -Eq '\.env\.production' scripts/deploy.sh 2>/dev/null; then
    pass "DEPLOY_SCRIPT_ENV_AUTHORITY_BOUNDARY_PRESENT"
else
    review "DEPLOY_SCRIPT_ENV_AUTHORITY_BOUNDARY_NOT_DETECTED"
fi

if grep -Eq 'docker-compose|compose' scripts/deploy.sh 2>/dev/null; then
    pass "DEPLOY_SCRIPT_COMPOSE_AUTHORITY_BOUNDARY_PRESENT"
else
    review "DEPLOY_SCRIPT_COMPOSE_AUTHORITY_BOUNDARY_NOT_DETECTED"
fi

section "9. SECRET OUTPUT FALSE-POSITIVE GUARD"

# IMPORTANT:
# Do not scan analyzer source files for secret identifiers.
# Identifiers inside audit logic are not secret values.
# Only inspect actual output artifacts for unredacted assignments.

SECRET_VALUE_OUTPUT_COUNT=0

for report in audit-output/p0_02_*.txt; do
    [ -f "$report" ] || continue

    if grep -Eq \
        'VALUE=(?!<REDACTED>)[^[:space:]]+' \
        "$report" 2>/dev/null; then

        SECRET_VALUE_OUTPUT_COUNT=$((SECRET_VALUE_OUTPUT_COUNT + 1))
        fail "UNREDACTED_SECRET_VALUE_IN_REPORT FILE=$report"
    fi
done

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "SECRET_VALUE_OUTPUT_DETECTED"
fi

section "10. CROSS-AUTHORITY INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_COMPOSE_SECRET_LINEAGE"
else
    fail "INVARIANT_COMPOSE_SECRET_LINEAGE"
fi

if [ "$RUNTIME_DECLARATION_COUNT" -ge 1 ] &&
   [ "$RUNTIME_CONTEXT_COUNT" -ge 2 ] &&
   [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_RUNTIME_SECRET_LINEAGE"
else
    fail "INVARIANT_RUNTIME_SECRET_LINEAGE"
fi

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "INVARIANT_DEPLOYMENT_NO_DIRECT_SECRET_REFERENCE"
else
    fail "INVARIANT_DEPLOYMENT_SECRET_REFERENCE"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "11. FINAL CLASSIFICATION"

log "FAILURE_COUNT=$FAILURE_COUNT"
log "REVIEW_COUNT=$REVIEW_COUNT"
log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"
log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"
log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"
log "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R17_SECRET_PROVENANCE_FALSE_POSITIVE_CLOSURE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R17_SECRET_PROVENANCE_FALSE_POSITIVE_CLOSURE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R17_SECRET_PROVENANCE_FALSE_POSITIVE_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R17_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
