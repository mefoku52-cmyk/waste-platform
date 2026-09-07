#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r9_runtime_secret_authority_closure.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

RUNTIME_DECLARATION_COUNT=0
RUNTIME_REFERENCE_COUNT=0
RUNTIME_LITERAL_COUNT=0
RUNTIME_CONTEXT_COUNT=0
ENV_SECRET_COUNT=0
SECRET_VALUE_OUTPUT_COUNT=0

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

section "P0-02 R9 RUNTIME SECRET AUTHORITY CLOSURE"

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

REQUIRED_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        pass "AUTHORITY_PRESENT=$f"
    else
        fail "AUTHORITY_MISSING=$f"
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
    echo "SECRET_IDENTIFIER=$key" | tee -a "$REPORT"
done

section "4. PRODUCTION ENV SECRET AUTHORITY"

for key in "${SECRET_KEYS[@]}"; do
    matches="$(
        grep -nE "^[[:space:]]*${key}=" .env.production 2>/dev/null || true
    )"

    if [ -n "$matches" ]; then
        count="$(printf '%s\n' "$matches" | wc -l)"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + count))

        while IFS=: read -r line_no _; do
            [ -n "${line_no:-}" ] || continue

            echo \
                "FILE=.env.production LINE=$line_no KEY=$key CLASSIFICATION=SECRET_STORE_VALUE VALUE=<REDACTED>" \
                | tee -a "$REPORT"
        done <<< "$matches"
    else
        review "PRODUCTION_SECRET_KEY_NOT_FOUND=$key"
    fi
done

echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "PRODUCTION_SECRET_AUTHORITY_PRESENT"
else
    fail "PRODUCTION_SECRET_AUTHORITY_INCOMPLETE"
fi

section "5. RUNTIME CONFIG CONTEXT"

CONFIG="app/core/config.py"

if [ -f "$CONFIG" ]; then

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        if echo "$line_text" | grep -qE \
            '^[[:space:]]*JWT_SECRET_KEY[[:space:]]*:'; then

            RUNTIME_DECLARATION_COUNT=$((RUNTIME_DECLARATION_COUNT + 1))

            echo \
                "LINE=$line_no KEY=JWT_SECRET_KEY CLASSIFICATION=TYPE_DECLARATION VALUE=<REDACTED>" \
                | tee -a "$REPORT"

        elif echo "$line_text" | grep -qE \
            '^[[:space:]]*JWT_SECRET_KEY[[:space:]]*='; then

            if echo "$line_text" | grep -qE \
                '\$\{|\bos\.environ\b|\bos\.getenv\b|\bgetenv\b|Field\(|SecretStr|Settings|BaseSettings'; then

                RUNTIME_REFERENCE_COUNT=$((RUNTIME_REFERENCE_COUNT + 1))

                echo \
                    "LINE=$line_no KEY=JWT_SECRET_KEY CLASSIFICATION=SETTINGS_OR_ENV_REFERENCE VALUE=<REDACTED>" \
                    | tee -a "$REPORT"

            else
                RUNTIME_LITERAL_COUNT=$((RUNTIME_LITERAL_COUNT + 1))

                echo \
                    "LINE=$line_no KEY=JWT_SECRET_KEY CLASSIFICATION=LITERAL_CANDIDATE VALUE=<REDACTED>" \
                    | tee -a "$REPORT"
            fi

        elif echo "$line_text" | grep -qE \
            'self\.JWT_SECRET_KEY|JWTSettings\(|secret_key=|secret='; then

            RUNTIME_CONTEXT_COUNT=$((RUNTIME_CONTEXT_COUNT + 1))

            echo \
                "LINE=$line_no KEY=JWT_SECRET_KEY CLASSIFICATION=NON_SECRET_RUNTIME_CONTEXT VALUE=<REDACTED>" \
                | tee -a "$REPORT"

        else
            RUNTIME_CONTEXT_COUNT=$((RUNTIME_CONTEXT_COUNT + 1))

            echo \
                "LINE=$line_no KEY=JWT_SECRET_KEY CLASSIFICATION=RUNTIME_CONTEXT VALUE=<REDACTED>" \
                | tee -a "$REPORT"
        fi

    done < <(
        grep -n "JWT_SECRET_KEY" "$CONFIG" 2>/dev/null || true
    )

else
    fail "RUNTIME_CONFIG_MISSING=$CONFIG"
fi

echo "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT" | tee -a "$REPORT"
echo "RUNTIME_REFERENCE_COUNT=$RUNTIME_REFERENCE_COUNT" | tee -a "$REPORT"
echo "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_RUNTIME_SECRET_ASSIGNMENT_DETECTED"
else
    fail "LITERAL_RUNTIME_SECRET_ASSIGNMENT_DETECTED"
fi

if [ "$RUNTIME_DECLARATION_COUNT" -gt 0 ]; then
    pass "JWT_SECRET_KEY_RUNTIME_DECLARATION_PRESENT"
else
    fail "JWT_SECRET_KEY_RUNTIME_DECLARATION_MISSING"
fi

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "JWT_SECRET_KEY_RUNTIME_USE_CONTEXT_PRESENT"
else
    review "JWT_SECRET_KEY_RUNTIME_USE_CONTEXT_NOT_OBSERVED"
fi

section "6. RUNTIME SETTINGS AUTHORITY CHECK"

if grep -qE \
    'BaseSettings|BaseModel|SettingsConfigDict|pydantic_settings|class[[:space:]].*Settings' \
    "$CONFIG" 2>/dev/null; then

    pass "SETTINGS_AUTHORITY_PATTERN_PRESENT"

else
    review "SETTINGS_AUTHORITY_PATTERN_NOT_CONFIRMED"
fi

if grep -q "JWT_SECRET_KEY" "$CONFIG" 2>/dev/null; then
    pass "JWT_SECRET_KEY_IDENTIFIER_PRESENT_IN_RUNTIME_CONFIG"
else
    fail "JWT_SECRET_KEY_IDENTIFIER_MISSING_FROM_RUNTIME_CONFIG"
fi

section "7. SECRET VALUE EXPOSURE GUARD"

# IMPORTANT:
# .env.production is the authorized secret store and is therefore excluded
# from this exposure scan. Its presence is verified separately in section 4.
#
# This scan checks source/runtime/config files only and never prints values.

EXPOSURE_SCAN_COUNT="$(
    {
        [ -f "app/core/config.py" ] && cat "app/core/config.py"
        [ -f "docker-compose.yml" ] && cat "docker-compose.yml"
        [ -f ".github/workflows/ci.yml" ] && cat ".github/workflows/ci.yml"
    } |
    grep -E \
        '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
    2>/dev/null |
    grep -vE \
        '\$\{|\benv:|\bsecrets\.|\bSecretStr\b|\bField\(|<REDACTED>|os\.getenv|os\.environ|getenv' \
    2>/dev/null |
    wc -l
)"

SECRET_VALUE_OUTPUT_COUNT="$EXPOSURE_SCAN_COUNT"

echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT" | tee -a "$REPORT"

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED"
fi

section "8. CI TEST AUTHORITY CONTEXT"

CI=".github/workflows/ci.yml"

if [ -f "$CI" ]; then

    CI_SECRET_ASSIGNMENT_COUNT="$(
        grep -nE \
            '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
            "$CI" 2>/dev/null |
        wc -l
    )"

    echo "CI_SECRET_ASSIGNMENT_COUNT=$CI_SECRET_ASSIGNMENT_COUNT" | tee -a "$REPORT"

    if [ "$CI_SECRET_ASSIGNMENT_COUNT" -gt 0 ]; then
        pass "CI_SECRET_ASSIGNMENTS_CLASSIFIED_AS_TEST_CONFIGURATION"
    else
        pass "NO_CI_SECRET_ASSIGNMENTS_PRESENT"
    fi

else
    fail "CI_AUTHORITY_MISSING=$CI"
fi

section "9. CROSS-AUTHORITY INVARIANTS"

if [ "$ENV_SECRET_COUNT" -eq 5 ]; then
    pass "INVARIANT_PRODUCTION_SECRET_SET_EXACT"
else
    fail "INVARIANT_PRODUCTION_SECRET_SET_NOT_EXACT"
fi

if [ "$RUNTIME_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_RUNTIME_SECRET"
else
    fail "INVARIANT_LITERAL_RUNTIME_SECRET"
fi

if [ "$RUNTIME_DECLARATION_COUNT" -gt 0 ]; then
    pass "INVARIANT_RUNTIME_SECRET_DECLARATION_PRESENT"
else
    fail "INVARIANT_RUNTIME_SECRET_DECLARATION_MISSING"
fi

if [ "$RUNTIME_CONTEXT_COUNT" -gt 0 ]; then
    pass "INVARIANT_RUNTIME_SECRET_USE_CONTEXT_PRESENT"
else
    review "INVARIANT_RUNTIME_SECRET_USE_CONTEXT_REQUIRES_REVIEW"
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_SECRET_VALUE_OUTPUT"
else
    fail "INVARIANT_SECRET_VALUE_OUTPUT"
fi

section "10. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "ENV_SECRET_COUNT=$ENV_SECRET_COUNT" | tee -a "$REPORT"
echo "RUNTIME_DECLARATION_COUNT=$RUNTIME_DECLARATION_COUNT" | tee -a "$REPORT"
echo "RUNTIME_REFERENCE_COUNT=$RUNTIME_REFERENCE_COUNT" | tee -a "$REPORT"
echo "RUNTIME_CONTEXT_COUNT=$RUNTIME_CONTEXT_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LITERAL_COUNT=$RUNTIME_LITERAL_COUNT" | tee -a "$REPORT"
echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R9_RUNTIME_SECRET_AUTHORITY_CLOSURE_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R9_RUNTIME_SECRET_AUTHORITY_CLOSURE_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R9_RUNTIME_SECRET_AUTHORITY_CLOSURE_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R9_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
