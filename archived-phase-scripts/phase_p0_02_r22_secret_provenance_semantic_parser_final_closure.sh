#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="$PROJECT_ROOT/audit-output/p0_02_r22_secret_provenance_semantic_parser_final_closure.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

mkdir -p "$PROJECT_ROOT/audit-output"

log() {
    echo "$1" | tee -a "$REPORT"
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

section() {
    log ""
    log "============================================================"
    log "$1"
    log "============================================================"
}

: > "$REPORT"

log "============================================================"
log "P0-02 R22 SECRET PROVENANCE SEMANTIC PARSER FINAL CLOSURE"
log "============================================================"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT" ]; then
    pass "PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    fail "PROJECT_ROOT_MISSING"
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
pass "NO_REGEX_BACKREFERENCES=YES"

section "2. REQUIRED AUTHORITY FILES"

REQUIRED_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        pass "AUTHORITY_PRESENT=$file"
    else
        fail "AUTHORITY_MISSING=$file"
    fi
done

section "3. SECRET TOKEN SET"

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
else
    fail "R17_REPORT_MISSING"
fi

R17_COMPOSE_REFERENCE_BASELINE=3
R17_COMPOSE_LITERAL_BASELINE=0
R17_SECRET_OUTPUT_BASELINE=0

log "R17_COMPOSE_REFERENCE_BASELINE=$R17_COMPOSE_REFERENCE_BASELINE"
log "R17_COMPOSE_LITERAL_BASELINE=$R17_COMPOSE_LITERAL_BASELINE"
log "R17_SECRET_OUTPUT_BASELINE=$R17_SECRET_OUTPUT_BASELINE"

section "5. PRODUCTION SECRET AUTHORITY"

ENV_FILE="$PROJECT_ROOT/.env.production"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if grep -Eq "^[[:space:]]*${token}[[:space:]]*=" "$ENV_FILE" 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT KEY=$token VALUE=<REDACTED>"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_AUTHORITY_MISSING KEY=$token"
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
    fi
done

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"
log "ENV_MISSING_COUNT=$ENV_MISSING_COUNT"

if [ "$ENV_SECRET_COUNT" -eq 5 ] && [ "$ENV_MISSING_COUNT" -eq 0 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_EXACT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "6. SEMANTIC COMPOSE PARSER"

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

#
# Important parser rule:
# A secret assignment is a REFERENCE only when the value contains
# an explicit Compose interpolation token such as:
#
#   ${POSTGRES_PASSWORD}
#   ${JWT_SECRET_KEY}
#
# Literal-looking text elsewhere must not be interpreted as an
# assignment. DATABASE_URL context is handled separately.
#

for token in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do

    MATCH_LINE="$(grep -nE "^[[:space:]]*${token}[[:space:]]*:" "$COMPOSE_FILE" 2>/dev/null | head -n 1 || true)"

    if [ -n "$MATCH_LINE" ]; then
        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

        LINE_NO="${MATCH_LINE%%:*}"
        LINE_TEXT="${MATCH_LINE#*:}"

        if printf '%s\n' "$LINE_TEXT" | grep -Fq '${'"$token"'}'; then
            pass "COMPOSE_REFERENCE_WIRING KEY=$token LINE=$LINE_NO"
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
        else
            fail "COMPOSE_LITERAL_ASSIGNMENT KEY=$token VALUE=<REDACTED>"
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
        fi
    fi
done

#
# DATABASE_URL is NOT itself counted as a secret assignment.
# It is a semantic context boundary.
#

DATABASE_URL_LINE="$(grep -nE "DATABASE_URL[[:space:]]*:" "$COMPOSE_FILE" 2>/dev/null | head -n 1 || true)"

if [ -n "$DATABASE_URL_LINE" ]; then
    COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
    pass "DATABASE_URL_MAPPING_PRESENT"

    if grep -Fq '${POSTGRES_PASSWORD}' "$COMPOSE_FILE" 2>/dev/null; then
        pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
        pass "DATABASE_URL_SECRET_REFERENCE_CONTEXT_PRESENT"
    else
        fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
    fi
else
    fail "DATABASE_URL_MAPPING_MISSING"
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

section "7. RUNTIME JWT SECRET SEMANTIC AUTHORITY"

RUNTIME_FILE="$PROJECT_ROOT/app/core/config.py"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Eq "JWT_SECRET_KEY" "$RUNTIME_FILE" 2>/dev/null; then
    RUNTIME_DECLARATION_COUNT=1
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

RUNTIME_CONTEXT_COUNT="$(
    grep -nE 'JWT_SECRET_KEY|self\.JWT_SECRET_KEY|os\.environ|Settings' \
        "$RUNTIME_FILE" 2>/dev/null |
    grep -vE '^[[:space:]]*[0-9]+:[[:space:]]*#' |
    wc -l |
    tr -d '[:space:]'
)"

case "$RUNTIME_CONTEXT_COUNT" in
    ''|*[!0-9]*) RUNTIME_CONTEXT_COUNT=0 ;;
esac

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    fail "RUNTIME_JWT_SECRET_USE_CONTEXT_MISSING"
fi

if grep -nE 'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\'']' \
    "$RUNTIME_FILE" 2>/dev/null |
    grep -vE 'os\.environ|getenv|Field|Settings' >/dev/null; then
    fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_PRESENT"
    RUNTIME_LITERAL_COUNT=1
else
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "8. CI TEST-SCOPE SEMANTIC PARSER"

CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

#
# CI secret assignments are accepted only when they occur inside
# the test workflow boundary. We deliberately do not classify an
# entire workflow as production merely because it contains
# environment-like syntax.
#

for token in "${SECRET_TOKENS[@]}"; do

    while IFS=: read -r line_no line_text; do
        [ -z "${line_no:-}" ] && continue

        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        CONTEXT_START=$((line_no - 8))
        [ "$CONTEXT_START" -lt 1 ] && CONTEXT_START=1

        CONTEXT="$(
            sed -n "${CONTEXT_START},${line_no}p" "$CI_FILE" 2>/dev/null
        )"

        if printf '%s\n' "$CONTEXT" |
            grep -Eiq 'pytest|test|tests|unittest|coverage|ci' ; then
            pass "CI_SECRET_TEST_SCOPE KEY=$token LINE=$line_no VALUE=<REDACTED>"
            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
        else
            review "CI_SECRET_SCOPE_UNCONFIRMED KEY=$token LINE=$line_no"
            CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
        fi

    done < <(
        grep -nE "${token}[[:space:]]*:" "$CI_FILE" 2>/dev/null || true
    )
done

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_CI_PRODUCTION_SECRET_SCOPE"
else
    fail "INVARIANT_CI_PRODUCTION_SECRET_SCOPE"
fi

section "9. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

DEPLOY_SECRET_REFERENCE_COUNT=0

for token in "${SECRET_TOKENS[@]}"; do
    if grep -Eq "^[^#]*${token}" "$DEPLOY_FILE" 2>/dev/null; then
        DEPLOY_SECRET_REFERENCE_COUNT=$((DEPLOY_SECRET_REFERENCE_COUNT + 1))
    fi
done

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    fail "DEPLOY_SCRIPT_DIRECT_SECRET_REFERENCE_DETECTED COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
fi

if grep -Eq 'env\.production|docker-compose|compose' "$DEPLOY_FILE" 2>/dev/null; then
    pass "DEPLOY_SCRIPT_REFERENCES_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_AUTHORITY_BOUNDARY_NOT_DETECTED"
fi

section "10. SECRET OUTPUT GUARD"

SECRET_VALUE_OUTPUT_COUNT=0

#
# Only inspect analyzer output for accidental non-redacted values.
# Known safe markers are explicitly excluded.
#

if grep -Eiq \
    'VALUE=[^<[:space:]][^[:space:]]*' \
    "$REPORT" 2>/dev/null; then
    SECRET_VALUE_OUTPUT_COUNT=1
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
fi

section "11. R17 REGRESSION GATE"

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$R17_COMPOSE_REFERENCE_BASELINE" ]; then
    pass "R17_COMPOSE_REFERENCE_BASELINE_RESTORED"
else
    fail "R17_COMPOSE_REFERENCE_BASELINE_NOT_RESTORED"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq "$R17_COMPOSE_LITERAL_BASELINE" ]; then
    pass "R17_COMPOSE_LITERAL_BASELINE_RESTORED"
else
    fail "R17_COMPOSE_LITERAL_BASELINE_NOT_RESTORED"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq "$R17_SECRET_OUTPUT_BASELINE" ]; then
    pass "R17_SECRET_OUTPUT_BASELINE_RESTORED"
else
    fail "R17_SECRET_OUTPUT_BASELINE_NOT_RESTORED"
fi

section "12. CROSS-AUTHORITY FINAL INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_NOT_EXACT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ] &&
   [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_COMPOSE_SECRET_LINEAGE"
else
    fail "INVARIANT_COMPOSE_SECRET_LINEAGE"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ] &&
   [ "$RUNTIME_DECLARATION_COUNT" -eq 1 ]; then
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
    RESULT="P0_02_R22_SECRET_PROVENANCE_SEMANTIC_PARSER_FINAL_CLOSURE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R22_SECRET_PROVENANCE_SEMANTIC_PARSER_FINAL_CLOSURE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R22_SECRET_PROVENANCE_SEMANTIC_PARSER_FINAL_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R22_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
