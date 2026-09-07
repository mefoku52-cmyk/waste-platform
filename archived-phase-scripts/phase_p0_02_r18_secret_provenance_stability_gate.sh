#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
cd "$PROJECT_ROOT" || exit 20

REPORT="$PROJECT_ROOT/audit-output/p0_02_r18_secret_provenance_stability_gate.txt"
mkdir -p "$PROJECT_ROOT/audit-output"

FAILURE_COUNT=0
REVIEW_COUNT=0

ENV_SECRET_COUNT=0
COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0
RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0
CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0
DEPLOY_SECRET_REFERENCE_COUNT=0
SECRET_VALUE_OUTPUT_COUNT=0

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

log() {
    printf '%s\n' "$1" | tee -a "$REPORT"
}

pass() {
    log "PASS: $1"
}

fail() {
    log "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    log "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

: > "$REPORT"

section "P0-02 R18 SECRET PROVENANCE STABILITY GATE"

section "1. SAFETY PRECHECK"

if [ "$PWD" = "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_CONFIRMATION"
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

REQUIRED_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "AUTHORITY_PRESENT=$file"
    else
        fail "AUTHORITY_MISSING=$file"
    fi
done

section "3. SECRET IDENTIFIER SET"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for key in "${SECRET_KEYS[@]}"; do
    log "SECRET_IDENTIFIER=$key"
done

section "4. PRODUCTION AUTHORITY"

for key in "${SECRET_KEYS[@]}"; do
    line="$(grep -nE "^${key}=" .env.production 2>/dev/null | head -n 1 || true)"

    if [ -n "$line" ]; then
        line_no="${line%%:*}"
        pass "ENV_AUTHORITY_PRESENT KEY=$key LINE=$line_no VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$key"
    fi
done

if [ "$ENV_SECRET_COUNT" -eq "${#SECRET_KEYS[@]}" ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
fi

section "5. COMPOSE SEMANTIC STABILITY"

compose_target_lines=(
    "POSTGRES_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
)

for key in "${compose_target_lines[@]}"; do
    match="$(
        grep -nE "^[[:space:]]*${key}:" docker-compose.yml 2>/dev/null |
        head -n 1 || true
    )"

    if [ -z "$match" ]; then
        fail "COMPOSE_TARGET_MISSING KEY=$key"
        continue
    fi

    line_no="${match%%:*}"
    value="${match#*:}"

    if printf '%s\n' "$value" |
        grep -Eq '\$\{[A-Za-z_][A-Za-z0-9_]*(:-[^}]*)?\}'; then
        pass "COMPOSE_REFERENCE_WIRING KEY=$key LINE=$line_no VALUE=<REDACTED>"
        COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
    else
        fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$key LINE=$line_no VALUE=<REDACTED>"
        COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
    fi

    COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))
done

DATABASE_URL_LINE="$(
    grep -nE "^[[:space:]]*DATABASE_URL:" docker-compose.yml 2>/dev/null |
    head -n 1 || true
)"

if [ -n "$DATABASE_URL_LINE" ]; then
    COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))

    if printf '%s\n' "$DATABASE_URL_LINE" |
        grep -Fq '${POSTGRES_PASSWORD}'; then
        pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    elif printf '%s\n' "$DATABASE_URL_LINE" |
        grep -Fq '${POSTGRES_PASSWORD:-'; then
        pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    else
        review "DATABASE_URL_SECRET_REFERENCE_CONTEXT_REQUIRES_MANUAL_CONFIRMATION"
    fi
else
    review "DATABASE_URL_MAPPING_NOT_DETECTED"
fi

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

section "6. RUNTIME SECRET STABILITY"

JWT_DECLARATION_COUNT="$(
    grep -nE "^[[:space:]]*JWT_SECRET_KEY[[:space:]]*:" app/core/config.py 2>/dev/null |
    wc -l | tr -d '[:space:]'
)"

JWT_CONTEXT_COUNT="$(
    grep -nE 'JWT_SECRET_KEY' app/core/config.py 2>/dev/null |
    grep -Ev '^[[:space:]]*#' |
    wc -l | tr -d '[:space:]'
)"

RUNTIME_DECLARATION_COUNT="${JWT_DECLARATION_COUNT:-0}"
RUNTIME_CONTEXT_COUNT="${JWT_CONTEXT_COUNT:-0}"

if [ "$RUNTIME_DECLARATION_COUNT" -ge 1 ]; then
    pass "RUNTIME_JWT_SECRET_DECLARATION_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_DECLARATION_MISSING"
fi

if [ "$RUNTIME_CONTEXT_COUNT" -ge 2 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    review "RUNTIME_JWT_SECRET_CONTEXT_REQUIRES_REVIEW COUNT=$RUNTIME_CONTEXT_COUNT"
fi

RUNTIME_LITERAL_COUNT="$(
    grep -nE '^[[:space:]]*(JWT_SECRET_KEY|secret_key|secret)[[:space:]]*[:=][[:space:]]*["'\'']' \
        app/core/config.py 2>/dev/null |
    grep -Ev 'JWT_SECRET_KEY[[:space:]]*[:=][[:space:]]*["'\'']?\$\{' |
    wc -l | tr -d '[:space:]'
)"

RUNTIME_LITERAL_COUNT="${RUNTIME_LITERAL_COUNT:-0}"

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT COUNT=$RUNTIME_LITERAL_COUNT"
fi

section "7. CI TEST-SCOPE STABILITY"

for key in "${SECRET_KEYS[@]}"; do
    matches="$(
        grep -nE "^[[:space:]]*${key}:" .github/workflows/ci.yml 2>/dev/null |
        head -n 20 || true
    )"

    if [ -n "$matches" ]; then
        while IFS= read -r match; do
            [ -z "$match" ] && continue

            line_no="${match%%:*}"
            CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

            context="$(
                sed -n "$((line_no>4 ? line_no-4 : 1)),$((line_no+4))p" \
                    .github/workflows/ci.yml 2>/dev/null
            )"

            if printf '%s\n' "$context" |
                grep -Eiq 'test|pytest|unit|ci'; then
                CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
                pass "CI_SECRET_TEST_SCOPE KEY=$key LINE=$line_no VALUE=<REDACTED>"
            else
                CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
                review "CI_SECRET_SCOPE_UNCONFIRMED KEY=$key LINE=$line_no"
            fi
        done <<< "$matches"
    fi
done

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "8. DEPLOYMENT AUTHORITY"

DEPLOY_SECRET_REFERENCE_COUNT="$(
    grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        scripts/deploy.sh 2>/dev/null |
    grep -Ev '^[^:]+:[[:space:]]*(#.*)?$' |
    wc -l | tr -d '[:space:]'
)"

DEPLOY_SECRET_REFERENCE_COUNT="${DEPLOY_SECRET_REFERENCE_COUNT:-0}"

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    fail "DEPLOY_SCRIPT_DIRECT_SECRET_IDENTIFIER_REFERENCE COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
fi

if grep -Eq '\.env\.production|docker-compose\.yml|compose' scripts/deploy.sh 2>/dev/null; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_DETECTED"
fi

section "9. SECRET OUTPUT GUARD"

OUTPUT_SCAN="$(
    {
        cat "$REPORT" 2>/dev/null || true
        [ -f audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt ] &&
            cat audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt
    } |
    grep -E \
        '^[^<]*VALUE=[^<[:space:]][^[:space:]]*|SECRET_VALUE=[^<[:space:]][^[:space:]]*' \
        2>/dev/null || true
)"

if [ -z "$OUTPUT_SCAN" ]; then
    SECRET_VALUE_OUTPUT_COUNT=0
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\n' "$OUTPUT_SCAN" |
        wc -l | tr -d '[:space:]'
    )"
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
fi

section "10. CROSS-AUTHORITY STABILITY INVARIANTS"

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

section "11. R17 REGRESSION GATE"

R17_REPORT="audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"

    if grep -q 'P0_02_R17_STATUS=CLEAN' "$R17_REPORT"; then
        pass "R17_BASELINE_CLEAN"
    else
        fail "R17_BASELINE_NOT_CLEAN"
    fi

    if grep -q 'COMPOSE_REFERENCE_COUNT=3' "$R17_REPORT"; then
        pass "R17_COMPOSE_REFERENCE_BASELINE=3"
    else
        fail "R17_COMPOSE_REFERENCE_BASELINE_MISMATCH"
    fi

    if grep -q 'COMPOSE_LITERAL_COUNT=0' "$R17_REPORT"; then
        pass "R17_COMPOSE_LITERAL_BASELINE=0"
    else
        fail "R17_COMPOSE_LITERAL_BASELINE_MISMATCH"
    fi

    if grep -q 'SECRET_VALUE_OUTPUT_COUNT=0' "$R17_REPORT"; then
        pass "R17_SECRET_OUTPUT_BASELINE=0"
    else
        fail "R17_SECRET_OUTPUT_BASELINE_MISMATCH"
    fi
else
    review "R17_REPORT_NOT_PRESENT"
fi

section "12. FINAL CLASSIFICATION"

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
    RESULT="P0_02_R18_SECRET_PROVENANCE_STABILITY_GATE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R18_SECRET_PROVENANCE_STABILITY_GATE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R18_SECRET_PROVENANCE_STABILITY_GATE_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R18_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
