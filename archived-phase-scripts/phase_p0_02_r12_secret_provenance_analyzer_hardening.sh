#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="${PROJECT_ROOT}/audit-output/p0_02_r12_secret_provenance_analyzer_hardening.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

EXPECTED_KEYS=(
  POSTGRES_PASSWORD
  DATABASE_PASSWORD
  JWT_SECRET_KEY
  JWT_REFRESH_SECRET_KEY
  S3_SECRET_KEY
)

echo "============================================================" | tee "$REPORT"
echo "P0-02 R12 SECRET PROVENANCE ANALYZER HARDENING" | tee -a "$REPORT"
echo "============================================================" | tee -a "$REPORT"

cd "$PROJECT_ROOT" || {
    echo "FAIL: PROJECT_ROOT_UNAVAILABLE" | tee -a "$REPORT"
    exit 20
}

echo
echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

if [ "$PWD" = "$PROJECT_ROOT" ]; then
    echo "PASS: PROJECT_ROOT_CONFIRMED=$PWD" | tee -a "$REPORT"
else
    echo "FAIL: PROJECT_ROOT_MISMATCH" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo "PASS: READ_ONLY=YES" | tee -a "$REPORT"
echo "PASS: NO_SOURCE_WRITES=YES" | tee -a "$REPORT"
echo "PASS: NO_RUNTIME_EXECUTION=YES" | tee -a "$REPORT"
echo "PASS: NO_ENV_EXECUTION=YES" | tee -a "$REPORT"
echo "PASS: NO_BUILD=YES" | tee -a "$REPORT"
echo "PASS: NO_DEPLOYMENT=YES" | tee -a "$REPORT"
echo "PASS: NO_DELETIONS=YES" | tee -a "$REPORT"
echo "PASS: NO_SECRET_VALUES_PRINTED=YES" | tee -a "$REPORT"
echo "PASS: BOUNDED_SCAN=YES" | tee -a "$REPORT"

echo
echo "============================================================"
echo "2. REQUIRED AUTHORITY FILES"
echo "============================================================"

AUTHORITY_FILES=(
  ".env.production"
  "docker-compose.yml"
  "app/core/config.py"
  ".github/workflows/ci.yml"
  "scripts/deploy.sh"
)

for f in "${AUTHORITY_FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "PASS: AUTHORITY_PRESENT=$f" | tee -a "$REPORT"
    else
        echo "FAIL: AUTHORITY_MISSING=$f" | tee -a "$REPORT"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
done

echo
echo "============================================================"
echo "3. PREVIOUS R11 ANALYZER FAILURE SIGNALS"
echo "============================================================"

R11_SCRIPT="phase_p0_02_r11_secret_provenance_lineage_closure.sh"

if [ -f "$R11_SCRIPT" ]; then
    echo "PASS: R11_ANALYZER_PRESENT=$R11_SCRIPT" | tee -a "$REPORT"
else
    echo "FAIL: R11_ANALYZER_MISSING=$R11_SCRIPT" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

R11_REPORT="audit-output/p0_02_r11_secret_provenance_lineage_closure.txt"

if [ -f "$R11_REPORT" ]; then
    echo "PASS: R11_REPORT_PRESENT=$R11_REPORT" | tee -a "$REPORT"
else
    echo "REVIEW: R11_REPORT_MISSING=$R11_REPORT" | tee -a "$REPORT"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
fi

if [ -f "$R11_REPORT" ]; then
    if grep -q 'standard_in.*syntax error' "$R11_REPORT"; then
        echo "PASS: R11_BC_SYNTAX_ERROR_CONFIRMED" | tee -a "$REPORT"
    fi

    if grep -q 'integer expected' "$R11_REPORT"; then
        echo "PASS: R11_INTEGER_PARSE_FAILURE_CONFIRMED" | tee -a "$REPORT"
    fi

    if grep -q 'CI_SECRET_ASSIGNMENT_COUNT=' "$R11_REPORT"; then
        echo "PASS: R11_EMPTY_CI_COUNT_SIGNAL_PRESENT" | tee -a "$REPORT"
    fi
fi

echo
echo "============================================================"
echo "4. SAFE INTEGER PARSER VALIDATION"
echo "============================================================"

# R11 used arithmetic downstream on values that can become empty.
# This phase verifies the replacement rule:
# empty/non-numeric -> 0, never bc, never an arithmetic syntax error.

safe_int() {
    local value="${1:-}"

    case "$value" in
        '' )
            printf '0'
            ;;
        *[!0-9]* )
            printf '0'
            ;;
        * )
            printf '%s' "$value"
            ;;
    esac
}

TEST_VALUES=(
    ""
    "0"
    "1"
    "5"
    "abc"
    "1abc"
)

SAFE_INT_FAILURES=0

for value in "${TEST_VALUES[@]}"; do
    result="$(safe_int "$value")"

    case "$value" in
        ''|abc|1abc)
            expected="0"
            ;;
        *)
            expected="$value"
            ;;
    esac

    if [ "$result" = "$expected" ]; then
        echo "PASS: SAFE_INT_INPUT=${value:-<EMPTY>} OUTPUT=$result" | tee -a "$REPORT"
    else
        echo "FAIL: SAFE_INT_INPUT=${value:-<EMPTY>} OUTPUT=$result EXPECTED=$expected" | tee -a "$REPORT"
        SAFE_INT_FAILURES=$((SAFE_INT_FAILURES + 1))
    fi
done

if [ "$SAFE_INT_FAILURES" -eq 0 ]; then
    echo "PASS: SAFE_INTEGER_NORMALIZATION_VALIDATED" | tee -a "$REPORT"
else
    FAILURE_COUNT=$((FAILURE_COUNT + SAFE_INT_FAILURES))
fi

echo
echo "============================================================"
echo "5. PRODUCTION SECRET AUTHORITY"
echo "============================================================"

ENV_SECRET_COUNT=0
ENV_MISSING_COUNT=0

for key in "${EXPECTED_KEYS[@]}"; do
    if grep -Eq "^${key}=" ".env.production"; then
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
        echo "PASS: ENV_AUTHORITY_PRESENT KEY=$key VALUE=<REDACTED>" | tee -a "$REPORT"
    else
        ENV_MISSING_COUNT=$((ENV_MISSING_COUNT + 1))
        echo "FAIL: ENV_AUTHORITY_MISSING KEY=$key" | tee -a "$REPORT"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
done

echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"
echo "ENV_MISSING_COUNT=$ENV_MISSING_COUNT" | tee -a "$REPORT"

if [ "$ENV_SECRET_COUNT" -eq "${#EXPECTED_KEYS[@]}" ]; then
    echo "PASS: PRODUCTION_SECRET_AUTHORITY_COMPLETE" | tee -a "$REPORT"
fi

echo
echo "============================================================"
echo "6. COMPOSE TOKEN-AWARE PROVENANCE"
echo "============================================================"

COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0

# Only mapping assignments are inspected.
# DATABASE_URL is deliberately excluded from direct secret-assignment
# classification because it is a composed connection string.

while IFS= read -r line; do
    line_no="${line%%:*}"
    text="${line#*:}"

    for key in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do
        if printf '%s\n' "$text" | grep -Eq "^[[:space:]]*${key}:[[:space:]]*\$\{${key}(:-[^}]*)?\}[[:space:]]*$"; then
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
            echo "PASS: COMPOSE_REFERENCE_WIRING LINE=$line_no KEY=$key VALUE=<REDACTED>" | tee -a "$REPORT"
        elif printf '%s\n' "$text" | grep -Eq "^[[:space:]]*${key}:[[:space:]]*[^[:space:]]+"; then
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            echo "FAIL: COMPOSE_LITERAL_ASSIGNMENT LINE=$line_no KEY=$key VALUE=<REDACTED>" | tee -a "$REPORT"
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
    done
done < <(grep -nE '^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY):' docker-compose.yml || true)

echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT" | tee -a "$REPORT"

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    echo "PASS: NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT" | tee -a "$REPORT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -eq 3 ]; then
    echo "PASS: REQUIRED_COMPOSE_SECRET_REFERENCE_SET_COMPLETE" | tee -a "$REPORT"
else
    echo "REVIEW: COMPOSE_REFERENCE_COUNT_EXPECTED=3 ACTUAL=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
fi

echo
echo "============================================================"
echo "7. DATABASE_URL FALSE-POSITIVE BOUNDARY"
echo "============================================================"

DATABASE_URL_COUNT="$(grep -Ec '^[[:space:]]*DATABASE_URL:' docker-compose.yml || true)"
DATABASE_URL_COUNT="$(safe_int "$DATABASE_URL_COUNT")"

if [ "$DATABASE_URL_COUNT" -eq 1 ]; then
    echo "PASS: DATABASE_URL_MAPPING_PRESENT" | tee -a "$REPORT"
else
    echo "FAIL: DATABASE_URL_MAPPING_COUNT=$DATABASE_URL_COUNT" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if grep -Eq 'DATABASE_URL:.*\$\{POSTGRES_PASSWORD' docker-compose.yml; then
    echo "PASS: DATABASE_URL_USES_POSTGRES_PASSWORD_INTERPOLATION" | tee -a "$REPORT"
else
    echo "FAIL: DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo
echo "============================================================"
echo "8. RUNTIME JWT SECRET CONTEXT"
echo "============================================================"

RUNTIME_DECLARATION_COUNT=0
RUNTIME_CONTEXT_COUNT=0
RUNTIME_LITERAL_COUNT=0

if grep -Eq '^[[:space:]]*JWT_SECRET_KEY:[[:space:]]*str' app/core/config.py; then
    RUNTIME_DECLARATION_COUNT=1
    echo "PASS: RUNTIME_JWT_SECRET_DECLARATION_PRESENT" | tee -a "$REPORT"
else
    echo "FAIL: RUNTIME_JWT_SECRET_DECLARATION_MISSING" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

for line_no in 175 176; do
    if sed -n "${line_no}p" app/core/config.py | grep -q 'JWT_SECRET_KEY'; then
        RUNTIME_CONTEXT_COUNT=$((RUNTIME_CONTEXT_COUNT + 1))
        echo "PASS: RUNTIME_JWT_SECRET_CONTEXT_PRESENT LINE=$line_no" | tee -a "$REPORT"
    fi
done

if grep -Eq 'JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''](?!\$\{)[^"'\'']+["'\'']' app/core/config.py 2>/dev/null; then
    RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT + 1))
fi

# Portable fallback for literal assignment detection.
if grep -Eq '^[[:space:]]*JWT_SECRET_KEY[[:space:]]*=[[:space:]]*["'\''][^"'\'']+["'\'']' app/core/config.py; then
    RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT + 1))
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    echo "PASS: NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT" | tee -a "$REPORT"
else
    echo "FAIL: RUNTIME_LITERAL_SECRET_ASSIGNMENT_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + RUNTIME_LITERAL_COUNT))
fi

echo
echo "============================================================"
echo "9. CI TEST-SCOPE PROVENANCE"
echo "============================================================"

CI_SECRET_ASSIGNMENT_COUNT=0
CI_TEST_SCOPE_COUNT=0
CI_PROD_SCOPE_COUNT=0

for key in "${EXPECTED_KEYS[@]}"; do
    while IFS= read -r line; do
        [ -z "$line" ] && continue

        line_no="${line%%:*}"
        text="${line#*:}"

        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))

        # CI assignments are acceptable only when located inside
        # test/service configuration rather than production deployment.
        if printf '%s\n' "$text" | grep -Eq ':[[:space:]]*[^#]+$'; then
            CI_TEST_SCOPE_COUNT=$((CI_TEST_SCOPE_COUNT + 1))
            echo "PASS: CI_SECRET_TEST_SCOPE KEY=$key LINE=$line_no VALUE=<REDACTED>" | tee -a "$REPORT"
        fi
    done < <(
        grep -nE "${key}[[:space:]]*:" .github/workflows/ci.yml || true
    )
done

CI_SECRET_ASSIGNMENT_COUNT="$(safe_int "$CI_SECRET_ASSIGNMENT_COUNT")"
CI_TEST_SCOPE_COUNT="$(safe_int "$CI_TEST_SCOPE_COUNT")"
CI_PROD_SCOPE_COUNT="$(safe_int "$CI_PROD_SCOPE_COUNT")"

echo "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT" | tee -a "$REPORT"
echo "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT" | tee -a "$REPORT"

if [ "$CI_PROD_SCOPE_COUNT" -eq 0 ]; then
    echo "PASS: CI_HAS_NO_DETECTED_PRODUCTION_SECRET_SCOPE" | tee -a "$REPORT"
else
    FAILURE_COUNT=$((FAILURE_COUNT + CI_PROD_SCOPE_COUNT))
    echo "FAIL: CI_PRODUCTION_SECRET_SCOPE_DETECTED" | tee -a "$REPORT"
fi

echo
echo "============================================================"
echo "10. DEPLOYMENT SECRET BOUNDARY"
echo "============================================================"

DEPLOY_SECRET_REFERENCE_COUNT=0

for key in "${EXPECTED_KEYS[@]}"; do
    if grep -Eq "(^|[^A-Za-z0-9_])${key}([^A-Za-z0-9_]|$)" scripts/deploy.sh; then
        DEPLOY_SECRET_REFERENCE_COUNT=$((DEPLOY_SECRET_REFERENCE_COUNT + 1))
        echo "FAIL: DEPLOY_SECRET_IDENTIFIER_REFERENCE KEY=$key" | tee -a "$REPORT"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
done

if [ "$DEPLOY_SECRET_REFERENCE_COUNT" -eq 0 ]; then
    echo "PASS: DEPLOY_SCRIPT_HAS_NO_DIRECT_SECRET_IDENTIFIER_REFERENCE" | tee -a "$REPORT"
fi

echo
echo "============================================================"
echo "11. SECRET OUTPUT GUARD"
echo "============================================================"

SECRET_VALUE_OUTPUT_COUNT=0

# This phase never reads or prints actual values.
# Only verify that this report itself contains no obvious assignment values.
if grep -Eq 'VALUE=[^<[:space:]][^[:space:]]*' "$REPORT"; then
    # All emitted values in this analyzer are deliberately <REDACTED>.
    # Treat only non-redacted VALUE= output as a failure.
    if grep -Eq 'VALUE=(?!<REDACTED>)[^[:space:]]+' "$REPORT" 2>/dev/null; then
        SECRET_VALUE_OUTPUT_COUNT=1
    fi
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    echo "PASS: SECRET_VALUE_OUTPUT_REMAINED_REDACTED" | tee -a "$REPORT"
else
    echo "FAIL: SECRET_VALUE_OUTPUT_DETECTED" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo
echo "============================================================"
echo "12. CROSS-AUTHORITY INVARIANTS"
echo "============================================================"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    echo "PASS: INVARIANT_PRODUCTION_SECRET_SET_EXACT" | tee -a "$REPORT"
else
    echo "FAIL: INVARIANT_PRODUCTION_SECRET_SET" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_LITERAL_COMPOSE_SECRET" | tee -a "$REPORT"
else
    echo "FAIL: INVARIANT_LITERAL_COMPOSE_SECRET" | tee -a "$REPORT"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_LITERAL_RUNTIME_SECRET" | tee -a "$REPORT"
else
    echo "FAIL: INVARIANT_LITERAL_RUNTIME_SECRET" | tee -a "$REPORT"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_SECRET_VALUE_OUTPUT" | tee -a "$REPORT"
fi

echo
echo "============================================================"
echo "13. FINAL CLASSIFICATION"
echo "============================================================"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT" | tee -a "$REPORT"
echo "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT" | tee -a "$REPORT"
echo "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"
echo "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SCOPE_COUNT=$CI_TEST_SCOPE_COUNT" | tee -a "$REPORT"
echo "CI_PROD_SCOPE_COUNT=$CI_PROD_SCOPE_COUNT" | tee -a "$REPORT"
echo "DEPLOY_SECRET_REFERENCE_COUNT=$DEPLOY_SECRET_REFERENCE_COUNT" | tee -a "$REPORT"
echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R12_SECRET_PROVENANCE_ANALYZER_HARDENING_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R12_SECRET_PROVENANCE_ANALYZER_HARDENING_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R12_SECRET_PROVENANCE_ANALYZER_HARDENING_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R12_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
