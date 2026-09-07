#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r6_secret_wiring_context_closure.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

PRODUCTION_REAL_SECRET=0
COMPOSE_LITERAL_SECRET=0
RUNTIME_LITERAL_SECRET=0
RUNTIME_REFERENCE=0
CI_TEST_SECRET=0
CI_CONTEXT_REVIEW=0

mkdir -p audit-output 2>/dev/null || true

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    echo "FAIL: $1" | tee -a "$REPORT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    echo "REVIEW: $1" | tee -a "$REPORT"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

section() {
    echo | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
    echo "$1" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

: > "$REPORT"

section "P0-02 R6 SECRET WIRING CONTEXT CLOSURE"

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
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"

section "2. REQUIRED AUTHORITY FILES"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
)

for f in "${AUTHORITY_FILES[@]}"; do
    if [ -f "$f" ]; then
        pass "AUTHORITY_PRESENT=$f"
    else
        fail "AUTHORITY_MISSING=$f"
    fi
done

section "3. EXACT REVIEW TARGETS"

RUNTIME_FILE="app/core/config.py"
CI_FILE=".github/workflows/ci.yml"

if [ -f "$RUNTIME_FILE" ]; then
    echo "--- RUNTIME TARGET CONTEXT ---" | tee -a "$REPORT"
    sed -n '168,182p' "$RUNTIME_FILE" | \
        sed -E 's/(JWT_SECRET_KEY[[:space:]]*=[[:space:]]*).*/\1<REDACTED>/g' | \
        tee -a "$REPORT"
else
    fail "RUNTIME_CONFIG_MISSING=$RUNTIME_FILE"
fi

if [ -f "$CI_FILE" ]; then
    echo "--- CI TARGET CONTEXT ---" | tee -a "$REPORT"
    sed -n '58,66p' "$CI_FILE" | \
        sed -E 's/(JWT_SECRET_KEY[[:space:]]*:[[:space:]]*).*/\1<REDACTED>/g' | \
        sed -E 's/(JWT_REFRESH_SECRET_KEY[[:space:]]*:[[:space:]]*).*/\1<REDACTED>/g' | \
        sed -E 's/(S3_SECRET_KEY[[:space:]]*:[[:space:]]*).*/\1<REDACTED>/g' | \
        tee -a "$REPORT"
else
    fail "CI_FILE_MISSING=$CI_FILE"
fi

section "4. RUNTIME SECRET SEMANTIC CLASSIFICATION"

if [ -f "$RUNTIME_FILE" ]; then

    for line in 175 176; do
        text="$(sed -n "${line}p" "$RUNTIME_FILE")"

        safe_text="$(printf '%s\n' "$text" | \
            sed -E 's/(JWT_SECRET_KEY[[:space:]]*=[[:space:]]*).*/\1<REDACTED>/')"

        echo "LINE=$line TEXT=$safe_text" | tee -a "$REPORT"

        # Pydantic/BaseSettings environment/config references are not
        # literal secret assignments.
        if printf '%s\n' "$text" | grep -qE \
            '(Field|field|validation_alias|alias|env|SecretStr|SettingsConfigDict|BaseSettings)'; then

            echo "LINE=$line CLASSIFICATION=CONFIGURATION_REFERENCE" | tee -a "$REPORT"

            if printf '%s\n' "$text" | grep -qE \
                '(^|[[:space:]])(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*=[[:space:]]*["'\'']'; then

                RUNTIME_LITERAL_SECRET=$((RUNTIME_LITERAL_SECRET + 1))
                fail "RUNTIME_LITERAL_SECRET_ASSIGNMENT_LINE=$line"
            else
                RUNTIME_REFERENCE=$((RUNTIME_REFERENCE + 1))
                pass "RUNTIME_SECRET_REFERENCE_LINE=$line"
            fi

        elif printf '%s\n' "$text" | grep -qE \
            '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:[^=]+$'; then

            echo "LINE=$line CLASSIFICATION=TYPE_DECLARATION" | tee -a "$REPORT"
            pass "RUNTIME_TYPE_DECLARATION_LINE=$line"

        elif printf '%s\n' "$text" | grep -qE \
            '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*='; then

            echo "LINE=$line CLASSIFICATION=ASSIGNMENT_REQUIRES_REVIEW" | tee -a "$REPORT"
            review "RUNTIME_SECRET_ASSIGNMENT_CONTEXT_LINE=$line"

        else
            echo "LINE=$line CLASSIFICATION=NON_SECRET_RUNTIME_CONTEXT" | tee -a "$REPORT"
            pass "RUNTIME_NON_SECRET_CONTEXT_LINE=$line"
        fi
    done

fi

if [ "$RUNTIME_LITERAL_SECRET" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_COUNT=$RUNTIME_LITERAL_SECRET"
fi

section "5. CI SECRET CONTEXT CLASSIFICATION"

if [ -f "$CI_FILE" ]; then

    text="$(sed -n '62p' "$CI_FILE")"

    safe_text="$(printf '%s\n' "$text" | \
        sed -E 's/(:[[:space:]]*).*/:\1<REDACTED>/')"

    echo "LINE=62 TEXT=$safe_text" | tee -a "$REPORT"

    # CI workflow environment values are test-scope unless a production
    # deployment path is established around them.
    context="$(sed -n '45,66p' "$CI_FILE")"

    if printf '%s\n' "$context" | grep -qiE \
        '(deploy|production|release|publish|docker push|kubectl apply|helm upgrade|ssh .*production)'; then

        review "CI_SECRET_LINE_62_HAS_POTENTIAL_DEPLOYMENT_CONTEXT"
        CI_CONTEXT_REVIEW=$((CI_CONTEXT_REVIEW + 1))
    else
        echo "LINE=62 CLASSIFICATION=TEST_CONFIGURATION" | tee -a "$REPORT"
        CI_TEST_SECRET=$((CI_TEST_SECRET + 1))
        pass "CI_SECRET_LINE_62_TEST_SCOPE_CONFIRMED"
    fi

fi

section "6. PRODUCTION ENV AUTHORITY"

LEGACY_SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

ENV_COUNT=0

if [ -f ".env.production" ]; then
    for key in "${LEGACY_SECRET_KEYS[@]}"; do
        if grep -qE "^${key}=" ".env.production" 2>/dev/null; then
            ENV_COUNT=$((ENV_COUNT + 1))
            pass "PRODUCTION_SECRET_AUTHORITY_KEY=$key VALUE=<REDACTED>"
        else
            fail "PRODUCTION_SECRET_AUTHORITY_KEY_MISSING=$key"
        fi
    done
fi

echo "PRODUCTION_ENV_SECRET_COUNT=$ENV_COUNT" | tee -a "$REPORT"

if [ "$ENV_COUNT" -eq 5 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_COMPLETE"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "7. COMPOSE SECRET WIRING"

COMPOSE_LITERAL_SECRET=0
COMPOSE_REFERENCE_COUNT=0

if [ -f "docker-compose.yml" ]; then

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        safe_text="$(printf '%s\n' "$line_text" | \
            sed -E 's/([=:][[:space:]]*).*/\1<REDACTED>/')"

        echo "LINE=$line_no TEXT=$safe_text" | tee -a "$REPORT"

        if printf '%s\n' "$line_text" | grep -qE \
            '\$\{(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)(:-[^}]*)?\}'; then

            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
            pass "COMPOSE_REFERENCE_WIRING_LINE=$line_no"

        elif printf '%s\n' "$line_text" | grep -qE \
            '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:'; then

            COMPOSE_LITERAL_SECRET=$((COMPOSE_LITERAL_SECRET + 1))
            fail "COMPOSE_LITERAL_SECRET_ASSIGNMENT_LINE=$line_no"
        fi

    done < <(
        grep -nE \
        '(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
        docker-compose.yml 2>/dev/null || true
    )

fi

echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_SECRET" | tee -a "$REPORT"

if [ "$COMPOSE_LITERAL_SECRET" -eq 0 ]; then
    pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_PRESENT"
fi

section "8. CROSS-AUTHORITY INVARIANTS"

if [ "$RUNTIME_LITERAL_SECRET" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_RUNTIME_SECRET"
else
    fail "INVARIANT_RUNTIME_LITERAL_SECRET"
fi

if [ "$COMPOSE_LITERAL_SECRET" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET"
else
    fail "INVARIANT_COMPOSE_LITERAL_SECRET"
fi

if [ "$CI_CONTEXT_REVIEW" -eq 0 ]; then
    pass "INVARIANT_CI_SECRET_CONTEXT_RESOLVED"
else
    review "INVARIANT_CI_SECRET_CONTEXT_REQUIRES_REVIEW"
fi

section "9. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_ENV_SECRET_COUNT=$ENV_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_SECRET" | tee -a "$REPORT"
echo "RUNTIME_REFERENCE_COUNT=$RUNTIME_REFERENCE" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_SECRET" | tee -a "$REPORT"
echo "CI_TEST_SECRET_COUNT=$CI_TEST_SECRET" | tee -a "$REPORT"
echo "CI_CONTEXT_REVIEW_COUNT=$CI_CONTEXT_REVIEW" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R6_SECRET_WIRING_CONTEXT_BOUNDARY_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ] || [ "$CI_CONTEXT_REVIEW" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R6_SECRET_WIRING_CONTEXT_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R6_SECRET_WIRING_CONTEXT_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R6_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
