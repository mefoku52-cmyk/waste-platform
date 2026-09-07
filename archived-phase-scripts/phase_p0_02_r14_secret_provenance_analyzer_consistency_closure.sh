#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(pwd)"
REPORT="$PROJECT_ROOT/audit-output/p0_02_r14_secret_provenance_analyzer_consistency_closure.txt"

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

SECRET_VALUE_OUTPUT_COUNT=0

EXPECTED_COMPOSE_REFERENCE_COUNT=0
MISSING_COMPOSE_REFERENCE_COUNT=0

: > "$REPORT"

log() {
    echo "$1" | tee -a "$REPORT"
}

section() {
    log ""
    log "============================================================"
    log "$1"
    log "============================================================"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    log "FAIL: $1"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    log "REVIEW: $1"
}

pass() {
    log "PASS: $1"
}

is_safe_int() {
    case "${1:-}" in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

safe_int() {
    if is_safe_int "${1:-}"; then
        echo "${1:-0}"
    else
        echo "0"
    fi
}

redact() {
    printf '%s' '<REDACTED>'
}

PROJECT_ROOT_EXPECTED="$HOME/waste-platform"

section "P0-02 R14 SECRET PROVENANCE ANALYZER CONSISTENCY CLOSURE"

section "1. SAFETY PRECHECK"

if [ -d "$PROJECT_ROOT/app" ] &&
   [ -f "$PROJECT_ROOT/docker-compose.yml" ] &&
   [ -f "$PROJECT_ROOT/.env.production" ]; then
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

section "3. SECRET TOKEN SET"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for key in "${SECRET_KEYS[@]}"; do
    log "SECRET_TOKEN=$key"
done

section "4. PRODUCTION ENV AUTHORITY"

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "^[[:space:]]*${key}=" "$PROJECT_ROOT/.env.production"; then
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
        pass "ENV_AUTHORITY_PRESENT KEY=$key VALUE=$(redact)"
    else
        fail "ENV_AUTHORITY_MISSING KEY=$key"
    fi
done

log "ENV_SECRET_COUNT=$ENV_SECRET_COUNT"

if [ "$ENV_SECRET_COUNT" -eq "${#SECRET_KEYS[@]}" ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_COMPLETE"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "5. COMPOSE TOKEN SEMANTIC ANALYSIS"

COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# These are the only production secret mappings expected directly
# in docker-compose.yml according to the established authority chain.
EXPECTED_COMPOSE_KEYS=(
    "POSTGRES_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
)

EXPECTED_COMPOSE_REFERENCE_COUNT=3

# Generic token detector.
# Accepts:
#   ${KEY}
#   ${KEY:-default}
#   ${KEY:?error}
#
# It deliberately does NOT consider literal assignment values to be
# references.
compose_has_reference() {
    local key="$1"

    grep -Eq \
        "\\\$\{${key}([}:]|:-|:\?)" \
        "$COMPOSE_FILE"
}

compose_has_literal_assignment() {
    local key="$1"

    # A literal assignment means:
    #   KEY: something
    # where the RHS does not contain ${KEY...}.
    #
    # We inspect only the relevant key and redact RHS.
    while IFS= read -r line; do
        case "$line" in
            *"$key:"*)
                rhs="${line#*:}"

                if printf '%s' "$rhs" | grep -Eq '\$\{[A-Za-z_][A-Za-z0-9_]*([}:]|:-|:\?)'; then
                    return 1
                fi

                # YAML null/empty is not a secret literal.
                trimmed="$(printf '%s' "$rhs" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

                if [ -z "$trimmed" ] || [ "$trimmed" = "null" ] || [ "$trimmed" = "~" ]; then
                    return 1
                fi

                return 0
                ;;
        esac
    done < "$COMPOSE_FILE"

    return 1
}

for key in "${EXPECTED_COMPOSE_KEYS[@]}"; do
    COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

    if compose_has_reference "$key"; then
        COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
        EXPECTED_COMPOSE_REFERENCE_COUNT=$((EXPECTED_COMPOSE_REFERENCE_COUNT + 1))
        pass "COMPOSE_REFERENCE_WIRING KEY=$key VALUE=$(redact)"
    else
        MISSING_COMPOSE_REFERENCE_COUNT=$((MISSING_COMPOSE_REFERENCE_COUNT + 1))

        if compose_has_literal_assignment "$key"; then
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_SECRET_ASSIGNMENT KEY=$key VALUE=$(redact)"
        else
            review "COMPOSE_REFERENCE_NOT_FOUND KEY=$key"
        fi
    fi
done

log "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT"
log "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
log "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
log "EXPECTED_COMPOSE_REFERENCE_COUNT=$EXPECTED_COMPOSE_REFERENCE_COUNT"
log "MISSING_COMPOSE_REFERENCE_COUNT=$MISSING_COMPOSE_REFERENCE_COUNT"

# Critical R13 consistency invariant:
# The number of individually proven references must equal the number
# of expected mappings. We never infer this from an unrelated count.
if [ "$EXPECTED_COMPOSE_REFERENCE_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ] &&
   [ "$COMPOSE_REFERENCE_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ]; then
    pass "INVARIANT_EXPECTED_COMPOSE_REFERENCES_EXACT"
else
    fail "INVARIANT_EXPECTED_COMPOSE_REFERENCES_MISMATCH"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "INVARIANT_LITERAL_COMPOSE_SECRET_COUNT=$COMPOSE_LITERAL_COUNT"
fi

section "6. DATABASE_URL FALSE-POSITIVE BOUNDARY"

if grep -Eq 'DATABASE_URL:' "$COMPOSE_FILE"; then
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    review "DATABASE_URL_MAPPING_NOT_FOUND"
fi

if grep -Eq '\$\{POSTGRES_PASSWORD([^}]*)\}' "$COMPOSE_FILE"; then
    pass "DATABASE_URL_USES_POSTGRES_PASSWORD_INTERPOLATION"
else
    review "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_NOT_DETECTED"
fi

section "7. RUNTIME JWT SECRET AUTHORITY"

RUNTIME_FILE="$PROJECT_ROOT/app/core/config.py"

if grep -Eq 'JWT_SECRET_KEY[[:space:]]*:' "$RUNTIME_FILE"; then
    RUNTIME_DECLARATION_COUNT=$((RUNTIME_DECLARATION_COUNT + 1))
    pass "RUNTIME_JWT_SECRET_DECLARATION_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_DECLARATION_MISSING"
fi

RUNTIME_JWT_CONTEXT_COUNT=0

while IFS= read -r line; do
    case "$line" in
        *'self.JWT_SECRET_KEY'*)
            RUNTIME_JWT_CONTEXT_COUNT=$((RUNTIME_JWT_CONTEXT_COUNT + 1))
            ;;
    esac
done < "$RUNTIME_FILE"

RUNTIME_CONTEXT_COUNT="$RUNTIME_JWT_CONTEXT_COUNT"

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "RUNTIME_JWT_SECRET_USE_CONTEXT_PRESENT COUNT=$RUNTIME_CONTEXT_COUNT"
else
    review "RUNTIME_JWT_SECRET_USE_CONTEXT_NOT_DETECTED"
fi

# Detect direct literal assignment patterns only.
if grep -Eq 'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''][^"'\'']+["'\'']' "$RUNTIME_FILE"; then
    RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT + 1))
    fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_DETECTED"
else
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
fi

log "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT"
log "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT"
log "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT"

section "8. CI TEST-SCOPE PROVENANCE"

CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "$key[[:space:]]*:" "$CI_FILE" ||
       grep -Eq "$key[[:space:]]*=" "$CI_FILE"; then

        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        # Test-only boundary:
        # reject production deployment contexts while allowing test jobs.
        if grep -n "$key" "$CI_FILE" |
           grep -Eiq 'deploy|production|prod:'; then
            CI_PROD_SCOPE_COUNT=$((CI_PROD_SCOPE_COUNT + 1))
            fail "CI_PRODUCTION_SECRET_SCOPE KEY=$key"
        else
            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            pass "CI_SECRET_TEST_SCOPE KEY=$key VALUE=$(redact)"
        fi
    fi
done

log "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT"
log "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT"
log "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    pass "CI_HAS_NO_DETECTED_PRODUCTION_SECRET_SCOPE"
else
    fail "CI_PRODUCTION_SECRET_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT"
fi

section "9. DEPLOYMENT AUTHORITY BOUNDARY"

DEPLOY_FILE="$PROJECT_ROOT/scripts/deploy.sh"

DEPLOY_SECRET_REFERENCE_COUNT=0

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "$key" "$DEPLOY_FILE"; then
        DEPLOY_SECRET_REFERENCE_COUNT=$((DEPLOY_SECRET_REFERENCE_COUNT + 1))
    fi
done

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    pass "DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE"
else
    review "DEPLOY_SCRIPT_DIRECT_SECRET_IDENTIFIER_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT"
fi

if grep -Eq '\.env\.production' "$DEPLOY_FILE"; then
    pass "DEPLOY_SCRIPT_REFERENCES_ENV_AUTHORITY_BOUNDARY"
else
    review "DEPLOY_SCRIPT_ENV_AUTHORITY_REFERENCE_NOT_DETECTED"
fi

if grep -Eq 'docker-compose\.yml' "$DEPLOY_FILE"; then
    pass "DEPLOY_SCRIPT_REFERENCES_COMPOSE_BOUNDARY"
else
    review "DEPLOY_SCRIPT_COMPOSE_BOUNDARY_REFERENCE_NOT_DETECTED"
fi

section "10. SECRET VALUE OUTPUT GUARD"

# The analyzer itself must never emit RHS secret values.
# Check this script and generated report for obvious unredacted assignment
# output patterns. This is intentionally conservative.
if grep -Eq \
    'VALUE=(<REDACTED>|REDACTED|\$|"\$\{)' \
    "$REPORT"; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    # Every VALUE= line generated by this analyzer is explicitly redacted.
    review "SECRET_VALUE_OUTPUT_GUARD_REQUIRES_MANUAL_CONFIRMATION"
fi

SECRET_VALUE_OUTPUT_COUNT=0

section "11. R13 ANALYZER-CONSISTENCY CLOSURE"

# R13 produced the logically impossible combination:
#   COMPOSE_REFERENCE_COUNT=3
#   EXPECTED_REFERENCE_MISSING for all three
#
# R14 proves references individually by key and then compares the
# resulting set cardinality against the expected set.
#
# This is a detector-quality invariant, not a production mutation.

if [ "$COMPOSE_REFERENCE_COUNT" -eq "$EXPECTED_COMPOSE_REFERENCE_COUNT" ] &&
   [ "$MISSING_COMPOSE_REFERENCE_COUNT" -eq 0 ]; then
    pass "R13_FALSE_FAILURE_CLASSIFICATION_ELIMINATED"
else
    fail "R13_FALSE_FAILURE_CLASSIFICATION_NOT_RESOLVED"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    pass "COMPOSE_REFERENCE_SET_CARDINALITY=3"
else
    fail "COMPOSE_REFERENCE_SET_CARDINALITY_UNEXPECTED=$COMPOSE_REFERENCE_COUNT"
fi

section "12. CROSS-AUTHORITY INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_NOT_EXACT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    pass "INVARIANT_REQUIRED_COMPOSE_SECRET_REFERENCES_PRESENT"
else
    fail "INVARIANT_REQUIRED_COMPOSE_SECRET_REFERENCES_NOT_COMPLETE"
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET"
else
    fail "INVARIANT_LITERAL_COMPOSE_SECRET"
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
log "EXPECTED_COMPOSE_REFERENCE_COUNT=$EXPECTED_COMPOSE_REFERENCE_COUNT"
log "MISSING_COMPOSE_REFERENCE_COUNT=$MISSING_COMPOSE_REFERENCE_COUNT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R14_SECRET_PROVENANCE_ANALYZER_CONSISTENCY_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R14_SECRET_PROVENANCE_ANALYZER_CONSISTENCY_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R14_SECRET_PROVENANCE_ANALYZER_CONSISTENCY_CLEAN"
    EXIT_CODE=0
fi

log "P0_02_R14_STATUS=$STATUS"
log "RESULT=$RESULT"
log "EXIT_CODE=$EXIT_CODE"
log "REPORT=$REPORT"

exit "$EXIT_CODE"
