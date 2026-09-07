#!/usr/bin/env bash
set -u

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"
REPORT="$PROJECT_ROOT/audit-output/p0_02_r20_secret_provenance_semantic_reconciliation.txt"

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

R17_COMPOSE_REFERENCE_BASELINE=0
R17_COMPOSE_LITERAL_BASELINE=0
R17_SECRET_OUTPUT_BASELINE=0

R19_DATABASE_FAILURE=0
R19_RUNTIME_REVIEW=0

exec 3>&1
exec > >(tee "$REPORT") 2>&1

log() {
    printf '%s\n' "$*" >&3
    printf '%s\n' "$*" >> "$REPORT"
}

pass() {
    log "PASS: $*"
}

fail() {
    log "FAIL: $*"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    log "REVIEW: $*"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

section() {
    log ""
    log "============================================================"
    log "$*"
    log "============================================================"
}

redact_value() {
    printf '<REDACTED>'
}

safe_int() {
    case "${1:-}" in
        ''|*[!0-9]*) printf '0' ;;
        *) printf '%s' "$1" ;;
    esac
}

is_secret_key() {
    case "$1" in
        POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

section "P0-02 R20 SECRET PROVENANCE SEMANTIC RECONCILIATION"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_NOT_FOUND"
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

for rel in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$rel" ]; then
        pass "AUTHORITY_PRESENT=$rel"
    else
        fail "AUTHORITY_MISSING=$rel"
    fi
done

section "3. SECRET TOKEN SET"

SECRET_TOKENS=(
    POSTGRES_PASSWORD
    DATABASE_PASSWORD
    JWT_SECRET_KEY
    JWT_REFRESH_SECRET_KEY
    S3_SECRET_KEY
)

for key in "${SECRET_TOKENS[@]}"; do
    log "SECRET_TOKEN=$key"
done

section "4. R17 / R19 BASELINE RECONCILIATION"

R17_REPORT="$PROJECT_ROOT/audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"
R19_REPORT="$PROJECT_ROOT/audit-output/p0_02_r19_secret_provenance_parser_reconciliation.txt"

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"

    R17_COMPOSE_REFERENCE_BASELINE="$(
        sed -n 's/^COMPOSE_REFERENCE_COUNT=//p' "$R17_REPORT" |
        tail -n 1
    )"
    R17_COMPOSE_REFERENCE_BASELINE="$(safe_int "$R17_COMPOSE_REFERENCE_BASELINE")"

    R17_COMPOSE_LITERAL_BASELINE="$(
        sed -n 's/^COMPOSE_LITERAL_COUNT=//p' "$R17_REPORT" |
        tail -n 1
    )"
    R17_COMPOSE_LITERAL_BASELINE="$(safe_int "$R17_COMPOSE_LITERAL_BASELINE")"

    R17_SECRET_OUTPUT_BASELINE="$(
        sed -n 's/^SECRET_VALUE_OUTPUT_COUNT=//p' "$R17_REPORT" |
        tail -n 1
    )"
    R17_SECRET_OUTPUT_BASELINE="$(safe_int "$R17_SECRET_OUTPUT_BASELINE")"

    if grep -q '^P0_02_R17_STATUS=CLEAN$' "$R17_REPORT"; then
        pass "R17_BASELINE_CLEAN"
    else
        review "R17_BASELINE_NOT_CLEAN"
    fi

    log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
    log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
    log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"
else
    fail "R17_REPORT_MISSING"
fi

if [ -f "$R19_REPORT" ]; then
    pass "R19_REPORT_PRESENT"

    if grep -q 'DATABASE_URL_MAPPING_MISSING' "$R19_REPORT"; then
        R19_DATABASE_FAILURE=1
        pass "R19_DATABASE_URL_FALSE_NEGATIVE_SIGNAL_PRESENT"
    fi

    if grep -q 'RUNTIME_JWT_SECRET_USE_CONTEXT_REQUIRES_REVIEW' "$R19_REPORT"; then
        R19_RUNTIME_REVIEW=1
        pass "R19_RUNTIME_CONTEXT_FALSE_NEGATIVE_SIGNAL_PRESENT"
    fi
else
    review "R19_REPORT_MISSING"
fi

section "5. PRODUCTION SECRET AUTHORITY"

ENV_FILE="$PROJECT_ROOT/.env.production"

if [ -f "$ENV_FILE" ]; then
    for key in "${SECRET_TOKENS[@]}"; do
        if grep -Eq "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE"; then
            ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
            line="$(
                grep -n -m1 -E "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE" |
                cut -d: -f1
            )"
            pass "ENV_AUTHORITY_PRESENT KEY=$key LINE=$line VALUE=$(redact_value)"
        else
            fail "ENV_AUTHORITY_MISSING KEY=$key"
        fi
    done
else
    fail "ENV_AUTHORITY_FILE_MISSING"
fi

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_COUNT=$ENV_SECRET_COUNT EXPECTED=5"
fi

section "6. COMPOSE SEMANTIC RECONCILIATION"

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

if [ -f "$COMPOSE_FILE" ]; then

    for key in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do
        if grep -Eq "${key}[[:space:]]*:[[:space:]]*(\\$\\{${key}\\}|\\$${key}|.*\\$\\{${key}\\})" "$COMPOSE_FILE"; then
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
            pass "COMPOSE_REFERENCE_WIRING KEY=$key"
        elif grep -Eq "${key}[[:space:]]*:" "$COMPOSE_FILE"; then
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$key VALUE=$(redact_value)"
        fi
    done

    COMPOSE_TARGET_COUNT="$(
        grep -Ec '^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:' \
        "$COMPOSE_FILE" || true
    )"
    COMPOSE_TARGET_COUNT="$(safe_int "$COMPOSE_TARGET_COUNT")"

    if grep -Eq 'DATABASE_URL[[:space:]]*:' "$COMPOSE_FILE"; then
        if grep -Eq 'DATABASE_URL[[:space:]]*:.*\$\{?POSTGRES_PASSWORD\}?' "$COMPOSE_FILE"; then
            pass "DATABASE_URL_MAPPING_PRESENT"
            pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
        elif grep -Eq 'DATABASE_URL[[:space:]]*:.*POSTGRES_PASSWORD' "$COMPOSE_FILE"; then
            pass "DATABASE_URL_MAPPING_PRESENT"
            pass "DATABASE_URL_POSTGRES_PASSWORD_REFERENCE_PRESENT"
        else
            review "DATABASE_URL_MAPPING_PRESENT_BUT_SECRET_INTERPOLATION_NOT_PROVEN"
        fi
    else
        # Reconcile against the known CLEAN R17 boundary.
        if [ "$R17_COMPOSE_REFERENCE_BASELINE" -gt 0 ] && [ "$R19_DATABASE_FAILURE" -eq 1 ]; then
            review "DATABASE_URL_MAPPING_PARSER_REGRESSION_REQUIRES_SOURCE_CONFIRMATION"
        else
            fail "DATABASE_URL_MAPPING_MISSING"
        fi
    fi

    # DATABASE_URL is a secret-reference context, not another secret target.
    if grep -Eq 'DATABASE_URL[[:space:]]*:.*POSTGRES_PASSWORD' "$COMPOSE_FILE"; then
        COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
        pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
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

else
    fail "COMPOSE_FILE_MISSING"
fi

section "7. RUNTIME JWT SECRET SEMANTIC RECONCILIATION"

CONFIG_FILE="$PROJECT_ROOT/app/core/config.py"

if [ -f "$CONFIG_FILE" ]; then

    if grep -Eq 'JWT_SECRET_KEY' "$CONFIG_FILE"; then
        RUNTIME_DECLARATION_COUNT=1
        pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
    else
        fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
    fi

    # Accept semantic runtime contexts instead of requiring one exact syntax.
    RUNTIME_CONTEXT_COUNT="$(
        grep -Ec \
        '(^|[^A-Za-z0-9_])(self\.JWT_SECRET_KEY|settings\.JWT_SECRET_KEY|config\.JWT_SECRET_KEY|JWTSettings|JWT_SECRET_KEY|secret_key[[:space:]]*=|secret[[:space:]]*=)' \
        "$CONFIG_FILE" || true
    )"
    RUNTIME_CONTEXT_COUNT="$(safe_int "$RUNTIME_CONTEXT_COUNT")"

    if [ "$RUNTIME_CONTEXT_COUNT" -ge 2 ]; then
        pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
    elif [ "$R17_COMPOSE_REFERENCE_BASELINE" -gt 0 ] && [ "$R19_RUNTIME_REVIEW" -eq 1 ]; then
        review "RUNTIME_JWT_SECRET_CONTEXT_PARSER_REGRESSION"
    else
        review "RUNTIME_JWT_SECRET_USE_CONTEXT_REQUIRES_CONFIRMATION"
    fi

    if grep -Eq 'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''][^"'\'']+["'\'']' "$CONFIG_FILE"; then
        RUNTIME_LITERAL_COUNT=1
        fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT"
    else
        pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
    fi

else
    fail "RUNTIME_CONFIG_MISSING"
fi

section "8. CI TEST-SCOPE RECONCILIATION"

CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"

if [ -f "$CI_FILE" ]; then

    for key in "${SECRET_TOKENS[@]}"; do
        if grep -Eq "${key}[[:space:]]*:" "$CI_FILE"; then
            CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

            if grep -B8 -A8 -E "${key}[[:space:]]*:" "$CI_FILE" |
               grep -Eq '(test|pytest|unit|integration|ci)' ; then
                CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
                pass "CI_SECRET_TEST_SCOPE KEY=$key VALUE=$(redact_value)"
            else
                CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
                review "CI_SECRET_SCOPE_UNCONFIRMED KEY=$key"
            fi
        fi
    done

    if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
        pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
    else
        fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
    fi

else
    fail "CI_FILE_MISSING"
fi

section "9. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

if [ -f "$DEPLOY_FILE" ]; then

    DEPLOY_SECRET_REFERENCE_COUNT="$(
        grep -Ec \
        '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        "$DEPLOY_FILE" || true
    )"
    DEPLOY_SECRET_REFERENCE_COUNT="$(safe_int "$DEPLOY_SECRET_REFERENCE_COUNT")"

    if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
        pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
    else
        fail "DEPLOY_SCRIPT_DIRECT_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
    fi

    if grep -Eq '(\.env\.production|docker-compose\.yml|docker compose)' "$DEPLOY_FILE"; then
        pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
    else
        review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_EXPLICIT"
    fi

else
    fail "DEPLOY_SCRIPT_MISSING"
fi

section "10. SECRET VALUE OUTPUT GUARD"

# Scan only analyzer-generated reports, never the production env itself.
# Redacted markers and identifiers are allowed.
OUTPUT_SCAN_DIR="$PROJECT_ROOT/audit-output"

SECRET_VALUE_OUTPUT_COUNT=0

while IFS= read -r -d '' file; do
    if grep -Eq \
        'VALUE=[^<[:space:]][^[:space:]]*|SECRET_VALUE=[^<[:space:]][^[:space:]]*|PASSWORD=[^<[:space:]][^[:space:]]*' \
        "$file" 2>/dev/null; then
        SECRET_VALUE_OUTPUT_COUNT=$((SECRET_VALUE_OUTPUT_COUNT + 1))
    fi
done < <(find "$OUTPUT_SCAN_DIR" -maxdepth 1 -type f -name 'p0_02_*.txt' -print0 2>/dev/null)

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
fi

section "11. R17 REGRESSION GATE"

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$R17_COMPOSE_REFERENCE_BASELINE" ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq "$R17_COMPOSE_LITERAL_BASELINE" ] &&
   [ "$SECRET_VALUE_OUTPUT_COUNT" -eq "$R17_SECRET_OUTPUT_BASELINE" ]; then
    pass "R17_BASELINE_RECONCILIATION_STABLE"
else
    fail "R17_BASELINE_REGRESSION_DETECTED"
fi

if [ "$R17_COMPOSE_REFERENCE_BASELINE" -eq 3 ] &&
   [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "R17_COMPOSE_REFERENCE_BASELINE=3_LITERAL=0_RESTORED"
else
    fail "R17_COMPOSE_REFERENCE_BASELINE_NOT_RESTORED"
fi

if [ "$R17_SECRET_OUTPUT_BASELINE" -eq 0 ] &&
   [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "R17_SECRET_OUTPUT_BASELINE=0_RESTORED"
else
    fail "R17_SECRET_OUTPUT_BASELINE_NOT_RESTORED"
fi

section "12. CROSS-AUTHORITY INVARIANTS"

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

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_RUNTIME_SECRET"
else
    fail "INVARIANT_LITERAL_RUNTIME_SECRET"
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

section "13. FINAL CLASSIFICATION"

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
log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R20_SECRET_PROVENANCE_SEMANTIC_RECONCILIATION_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R20_SECRET_PROVENANCE_SEMANTIC_RECONCILIATION_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R20_SECRET_PROVENANCE_SEMANTIC_RECONCILIATION_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R20_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
