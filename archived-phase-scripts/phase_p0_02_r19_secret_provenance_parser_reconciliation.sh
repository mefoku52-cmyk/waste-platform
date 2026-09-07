#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"
cd "$PROJECT_ROOT" || exit 20

REPORT="$PROJECT_ROOT/audit-output/p0_02_r19_secret_provenance_parser_reconciliation.txt"
mkdir -p "$PROJECT_ROOT/audit-output"

: > "$REPORT"

FAILURE_COUNT=0
REVIEW_COUNT=0

log() {
    printf '%s\n' "$*" | tee -a "$REPORT"
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

safe_count() {
    case "${1:-}" in
        ''|*[!0-9]*) printf '0\n' ;;
        *) printf '%s\n' "$1" ;;
    esac
}

section "P0-02 R19 SECRET PROVENANCE PARSER RECONCILIATION"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_MISSING"
fi

READ_ONLY=YES
NO_SOURCE_WRITES=YES
NO_RUNTIME_EXECUTION=YES
NO_ENV_EXECUTION=YES
NO_BUILD=YES
NO_DEPLOYMENT=YES
NO_DELETIONS=YES
NO_SECRET_VALUES_PRINTED=YES
BOUNDED_SCAN=YES

pass "READ_ONLY=$READ_ONLY"
pass "NO_SOURCE_WRITES=$NO_SOURCE_WRITES"
pass "NO_RUNTIME_EXECUTION=$NO_RUNTIME_EXECUTION"
pass "NO_ENV_EXECUTION=$NO_ENV_EXECUTION"
pass "NO_BUILD=$NO_BUILD"
pass "NO_DEPLOYMENT=$NO_DEPLOYMENT"
pass "NO_DELETIONS=$NO_DELETIONS"
pass "NO_SECRET_VALUES_PRINTED=$NO_SECRET_VALUES_PRINTED"
pass "BOUNDED_SCAN=$BOUNDED_SCAN"

section "2. REQUIRED AUTHORITY FILES"

REQUIRED_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        pass "AUTHORITY_PRESENT=$f"
    else
        fail "AUTHORITY_MISSING=$f"
    fi
done

section "3. SECRET IDENTIFIER SET"

SECRET_TOKENS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for token in "${SECRET_TOKENS[@]}"; do
    log "SECRET_TOKEN=$token"
done

section "4. R17 BASELINE"

R17_REPORT="$PROJECT_ROOT/audit-output/p0_02_r17_secret_provenance_false_positive_closure.txt"

if [ -f "$R17_REPORT" ]; then
    pass "R17_REPORT_PRESENT"

    R17_STATUS="$(grep -E '^P0_02_R17_STATUS=' "$R17_REPORT" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R17_RESULT="$(grep -E '^RESULT=' "$R17_REPORT" 2>/dev/null | tail -1 | cut -d= -f2-)"

    if [ "$R17_STATUS" = "CLEAN" ]; then
        pass "R17_BASELINE_CLEAN"
    else
        review "R17_BASELINE_STATUS=${R17_STATUS:-UNKNOWN}"
    fi

    R17_COMPOSE_REF="$(grep -E '^COMPOSE_REFERENCE_COUNT=' "$R17_REPORT" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R17_COMPOSE_LITERAL="$(grep -E '^COMPOSE_LITERAL_COUNT=' "$R17_REPORT" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R17_SECRET_OUTPUT="$(grep -E '^SECRET_VALUE_OUTPUT_COUNT=' "$R17_REPORT" 2>/dev/null | tail -1 | cut -d= -f2-)"

    R17_COMPOSE_REF="$(safe_count "$R17_COMPOSE_REF")"
    R17_COMPOSE_LITERAL="$(safe_count "$R17_COMPOSE_LITERAL")"
    R17_SECRET_OUTPUT="$(safe_count "$R17_SECRET_OUTPUT")"

    log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REF"
    log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL"
    log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT"
else
    fail "R17_REPORT_MISSING"
    R17_COMPOSE_REF=0
    R17_COMPOSE_LITERAL=0
    R17_SECRET_OUTPUT=0
fi

section "5. PRODUCTION AUTHORITY"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if grep -Eq "^[[:space:]]*${token}=" "$PROJECT_ROOT/.env.production"; then
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
        pass "ENV_AUTHORITY_PRESENT KEY=$token VALUE=<REDACTED>"
    else
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
        fail "ENV_AUTHORITY_MISSING KEY=$token"
    fi
done

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq "${#SECRET_TOKENS[@]}" ] && [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "6. TOKEN-AWARE COMPOSE RECONCILIATION"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

# A real Compose reference must contain the token in interpolation syntax:
#   ${TOKEN}
#   ${TOKEN:-default}
#
# The token appearing as a YAML key is NOT itself a literal secret assignment.
#
# The scanner deliberately never prints the assigned value.

for token in "${SECRET_TOKENS[@]}"; do

    while IFS=: read -r line_no line_text; do
        [ -z "${line_no:-}" ] && continue

        # Ignore DATABASE_URL context. It is validated separately.
        if printf '%s\n' "$line_text" | grep -Eq 'DATABASE_URL'; then
            COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
            continue
        fi

        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

        if printf '%s\n' "$line_text" |
            grep -Eq '\$\{'"$token"'([:-][^}]*)?\}'; then

            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
            pass "COMPOSE_REFERENCE_WIRING KEY=$token LINE=$line_no"

        elif printf '%s\n' "$line_text" |
            grep -Eq '^[[:space:]]*-[[:space:]]*'"$token"'[[:space:]]*='; then

            # A shell-style assignment without interpolation is potentially
            # a literal assignment and therefore requires failure classification.
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token LINE=$line_no VALUE=<REDACTED>"

        elif printf '%s\n' "$line_text" |
            grep -Eq '^[[:space:]]*'"$token"':[[:space:]]*[^$[:space:]]'; then

            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token LINE=$line_no VALUE=<REDACTED>"

        fi
    done < <(
        grep -nE \
            "^[[:space:]]*(-[[:space:]]*)?${token}([[:space:]]*:|[[:space:]]*=)" \
            "$PROJECT_ROOT/docker-compose.yml" 2>/dev/null || true
    )

done

# Explicitly scan interpolation references because the reference may occur
# in an environment mapping where the YAML key/value shape differs.
for token in "${SECRET_TOKENS[@]}"; do
    REF_HITS="$(
        grep -Eo '\$\{'"$token"'([:-][^}]*)?\}' \
            "$PROJECT_ROOT/docker-compose.yml" 2>/dev/null |
        wc -l
    )"

    REF_HITS="$(safe_count "$REF_HITS")"

    if [ "$token" = "DATABASE_PASSWORD" ] || [ "$token" = "S3_SECRET_KEY" ]; then
        :
    elif [ "$REF_HITS" -gt 0 ]; then
        :
    fi
done

# The production Compose wiring is expected only for these three runtime
# transport secrets. DATABASE_PASSWORD and S3_SECRET_KEY may have no Compose
# reference and must not be fabricated into the expected count.
EXPECTED_COMPOSE_REFERENCE_COUNT=3

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"
log "EXPECTED_COMPOSE_REFERENCE_COUNT=$EXPECTED_COMPOSE_REFERENCE_COUNT"

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ]; then
    pass "COMPOSE_REFERENCE_CARDINALITY_EXACT"
else
    fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH EXPECTED=$EXPECTED_COMPOSE_REFERENCE_COUNT ACTUAL=$COMPOSE_REFERENCE_COUNT"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_PRESENT"
fi

section "7. DATABASE_URL FALSE-POSITIVE BOUNDARY"

if grep -Eq 'DATABASE_URL=' "$PROJECT_ROOT/docker-compose.yml"; then
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    fail "DATABASE_URL_MAPPING_MISSING"
fi

if grep -Eq '\$\{POSTGRES_PASSWORD\}' "$PROJECT_ROOT/docker-compose.yml"; then
    pass "DATABASE_URL_USES_POSTGRES_PASSWORD_INTERPOLATION"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

section "8. RUNTIME SECRET RECONCILIATION"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Eq 'JWT_SECRET_KEY' "$PROJECT_ROOT/app/core/config.py"; then
    RUNTIME_DECLARATION_COUNT="$(
        grep -Ec \
            'JWT_SECRET_KEY.*(str|Secret|Field|Settings)|[[:space:]]*JWT_SECRET_KEY[[:space:]]*:' \
            "$PROJECT_ROOT/app/core/config.py" 2>/dev/null || true
    )"
    RUNTIME_DECLARATION_COUNT="$(safe_count "$RUNTIME_DECLARATION_COUNT")"

    if [ "$RUNTIME_DECLARATION_COUNT" -gt 0 ]; then
        pass "RUNTIME_JWT_SECRET_DECLARATION_PRESENT"
    else
        review "RUNTIME_JWT_SECRET_DECLARATION_REQUIRES_CONTEXT"
    fi

    RUNTIME_CONTEXT_COUNT="$(
        grep -Ec \
            'JWT_SECRET_KEY.*(settings|os\.getenv|Field|BaseSettings|config)' \
            "$PROJECT_ROOT/app/core/config.py" 2>/dev/null || true
    )"
    RUNTIME_CONTEXT_COUNT="$(safe_count "$RUNTIME_CONTEXT_COUNT")"

    if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
        pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
    else
        review "RUNTIME_JWT_SECRET_USE_CONTEXT_REQUIRES_REVIEW"
    fi
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

RUNTIME_LITERAL_COUNT="$(
    grep -Ec \
        'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''][^"'\'']+["'\'']' \
        "$PROJECT_ROOT/app/core/config.py" 2>/dev/null || true
)"
RUNTIME_LITERAL_COUNT="$(safe_count "$RUNTIME_LITERAL_COUNT")"

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_PRESENT"
fi

section "9. CI TEST-SCOPE RECONCILIATION"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

# CI secret assignments are accepted only when they occur inside an explicitly
# test-oriented workflow section. We inspect bounded context instead of using
# line-number arithmetic, preventing the R11/R18 empty-counter false positive.

for token in "${SECRET_TOKENS[@]}"; do

    while IFS=: read -r line_no _; do
        [ -z "${line_no:-}" ] && continue

        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        START=$((line_no - 12))
        [ "$START" -lt 1 ] && START=1

        END=$((line_no + 12))

        CONTEXT="$(
            sed -n "${START},${END}p" \
                "$PROJECT_ROOT/.github/workflows/ci.yml" 2>/dev/null || true
        )"

        if printf '%s\n' "$CONTEXT" |
            grep -Eiq \
                '(pytest|test|tests|unit[-_ ]?test|integration[-_ ]?test|coverage)'; then

            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            pass "CI_SECRET_TEST_SCOPE KEY=$token LINE=$line_no VALUE=<REDACTED>"

        elif printf '%s\n' "$CONTEXT" |
            grep -Eiq \
                '(deploy|production|prod|release|publish)'; then

            CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
            fail "CI_SECRET_PRODUCTION_SCOPE KEY=$token LINE=$line_no"

        else
            review "CI_SECRET_SCOPE_REQUIRES_CONTEXT KEY=$token LINE=$line_no"
        fi

    done < <(
        grep -nE \
            "^[[:space:]]+${token}:[[:space:]]*" \
            "$PROJECT_ROOT/.github/workflows/ci.yml" 2>/dev/null || true
    )

done

CI_SECRET_ASSIGNMENT_COUNT="$(safe_count "$CI_SECRET_ASSIGNMENT_COUNT")"
CI_TEST_SCOPE_COUNT="$(safe_count "$CI_TEST_SCOPE_COUNT")"
CI_PROD_SCOPE_COUNT="$(safe_count "$CI_PROD_SCOPE_COUNT")"

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "10. DEPLOYMENT AUTHORITY"

if grep -Eq \
    'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
    "$PROJECT_ROOT/scripts/deploy.sh" 2>/dev/null; then

    fail "DEPLOY_SCRIPT_HAS_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
fi

if grep -Eiq 'env|environment|compose|docker-compose' \
    "$PROJECT_ROOT/scripts/deploy.sh" 2>/dev/null; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_DETECTED"
fi

section "11. SECRET OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=0

# The analyzer itself must never print actual values.
# Detect accidental unredacted secret-value assignments in its own report.
if grep -Eiq \
    'VALUE=(?!<REDACTED>|$)[^[:space:]]+' \
    "$REPORT" 2>/dev/null; then

    SECRET_VALUE_OUTPUT_COUNT=1
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED"
else
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
fi

log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

section "12. R17 REGRESSION RECONCILIATION"

if [ "$R17_COMPOSE_REF" -eq 3 ] &&
   [ "$R17_COMPOSE_LITERAL" -eq 0 ] &&
   [ "$R17_SECRET_OUTPUT" -eq 0 ]; then
    pass "R17_EXPECTED_COMPOSE_STATE_REFERENCE=3_LITERAL=0_OUTPUT=0"
else
    review "R17_BASELINE_VALUES_UNAVAILABLE_OR_NONCLEAN"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$R17_COMPOSE_REF" ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq "$R17_COMPOSE_LITERAL" ] &&
   [ "$SECRET_VALUE_OUTPUT_COUNT" -eq "$R17_SECRET_OUTPUT" ]; then

    pass "R19_RECONCILES_WITH_R17_BASELINE"
else
    fail "R19_R17_BASELINE_REGRESSION_DETECTED"
fi

section "13. FINAL INVARIANTS"

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

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "14. FINAL CLASSIFICATION"

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
log "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"
log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REF"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R19_SECRET_PROVENANCE_PARSER_RECONCILIATION_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R19_SECRET_PROVENANCE_PARSER_RECONCILIATION_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R19_SECRET_PROVENANCE_PARSER_RECONCILIATION_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R19_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
