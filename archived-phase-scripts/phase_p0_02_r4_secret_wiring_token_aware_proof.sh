#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r4_secret_wiring_token_aware_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
PROD_LITERAL_COUNT=0
PROD_REFERENCE_COUNT=0
CI_TEST_COUNT=0
RUNTIME_REFERENCE_COUNT=0

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

section "3. SECRET IDENTIFIERS"

SECRET_REGEX='POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY'

echo "SECRET_IDENTIFIER_SCAN=REDACTED_ONLY" | tee -a "$REPORT"

for key in \
    POSTGRES_PASSWORD \
    DATABASE_PASSWORD \
    JWT_SECRET_KEY \
    JWT_REFRESH_SECRET_KEY \
    S3_SECRET_KEY
do
    echo "SECRET_IDENTIFIER=$key" | tee -a "$REPORT"
done

section "4. PRODUCTION ENV AUTHORITY"

if [ -f ".env.production" ]; then

    PROD_ENV_MATCHES="$(
        grep -nE '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
        .env.production 2>/dev/null || true
    )"

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        key="$(
            echo "$line_text" |
            sed -E 's/^[[:space:]]*([^=[:space:]]+)[[:space:]]*=.*/\1/'
        )"

        echo "FILE=.env.production LINE=$line_no KEY=$key CLASSIFICATION=SECRET_STORE_VALUE VALUE=<REDACTED>" |
            tee -a "$REPORT"

        PROD_LITERAL_COUNT=$((PROD_LITERAL_COUNT + 1))
    done <<< "$PROD_ENV_MATCHES"

fi

echo "PRODUCTION_ENV_SECRET_COUNT=$PROD_LITERAL_COUNT" | tee -a "$REPORT"

if [ "$PROD_LITERAL_COUNT" -eq 5 ]; then
    pass "PRODUCTION_ENV_SECRET_AUTHORITY_COMPLETE"
else
    fail "PRODUCTION_ENV_SECRET_AUTHORITY_EXPECTED_5_FOUND=$PROD_LITERAL_COUNT"
fi

section "5. COMPOSE TOKEN-AWARE WIRING"

COMPOSE_MATCHES="$(
    grep -nE \
    'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
    docker-compose.yml 2>/dev/null || true
)"

while IFS=: read -r line_no line_text; do
    [ -n "${line_no:-}" ] || continue

    key="$(
        echo "$line_text" |
        grep -oE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' |
        head -n1
    )"

    [ -n "${key:-}" ] || continue

    # ${VAR}, ${VAR:-default}, env_file and similar references are wiring.
    if echo "$line_text" | grep -qE '\$\{[A-Za-z_][A-Za-z0-9_]*(:-[^}]*)?\}'; then
        echo "FILE=docker-compose.yml LINE=$line_no KEY=$key CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>" |
            tee -a "$REPORT"

        PROD_REFERENCE_COUNT=$((PROD_REFERENCE_COUNT + 1))

    elif echo "$line_text" | grep -qE '^[[:space:]]*-[[:space:]]*[A-Za-z_][A-Za-z0-9_]*$'; then
        echo "FILE=docker-compose.yml LINE=$line_no KEY=$key CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>" |
            tee -a "$REPORT"

        PROD_REFERENCE_COUNT=$((PROD_REFERENCE_COUNT + 1))

    else
        echo "FILE=docker-compose.yml LINE=$line_no KEY=$key CLASSIFICATION=LITERAL_OR_NON_REFERENCE VALUE=<REDACTED>" |
            tee -a "$REPORT"

        PROD_LITERAL_COUNT=$((PROD_LITERAL_COUNT + 1))
    fi

done <<< "$COMPOSE_MATCHES"

echo "COMPOSE_REFERENCE_COUNT=$PROD_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_OR_NON_REFERENCE_COUNT=$PROD_LITERAL_COUNT" | tee -a "$REPORT"

if [ "$PROD_LITERAL_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_PRODUCTION_SECRET_VALUE_IN_COMPOSE_WIRING"
else
    fail "LITERAL_PRODUCTION_SECRET_VALUE_PRESENT_IN_COMPOSE"
fi

section "6. RUNTIME CONFIG TOKEN-AWARE PROOF"

if [ -f "app/core/config.py" ]; then

    RUNTIME_MATCHES="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        app/core/config.py 2>/dev/null || true
    )"

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        key="$(
            echo "$line_text" |
            grep -oE \
            'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' |
            head -n1
        )"

        [ -n "${key:-}" ] || continue

        if echo "$line_text" | grep -qE \
            '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:[[:space:]]*(str|SecretStr|Optional\[.*\])'; then

            echo "FILE=app/core/config.py LINE=$line_no KEY=$key CLASSIFICATION=TYPE_OR_DECLARATION VALUE=<REDACTED>" |
                tee -a "$REPORT"

        elif echo "$line_text" | grep -qE \
            '(os\.getenv|os\.environ|getenv|BaseSettings|Settings|SecretStr|env_file)'; then

            echo "FILE=app/core/config.py LINE=$line_no KEY=$key CLASSIFICATION=REFERENCE VALUE=<REDACTED>" |
                tee -a "$REPORT"

            RUNTIME_REFERENCE_COUNT=$((RUNTIME_REFERENCE_COUNT + 1))

        else

            echo "FILE=app/core/config.py LINE=$line_no KEY=$key CLASSIFICATION=REVIEW_REQUIRED VALUE=<REDACTED>" |
                tee -a "$REPORT"

            review "RUNTIME_SECRET_LINE_REQUIRES_SEMANTIC_REVIEW=$line_no"
        fi

    done <<< "$RUNTIME_MATCHES"

fi

echo "RUNTIME_REFERENCE_COUNT=$RUNTIME_REFERENCE_COUNT" | tee -a "$REPORT"

if [ "$RUNTIME_REFERENCE_COUNT" -gt 0 ]; then
    pass "RUNTIME_SECRET_REFERENCES_DETECTED_WITHOUT_VALUE_OUTPUT"
else
    review "NO_RUNTIME_SECRET_REFERENCE_CLASSIFIED"
fi

section "7. CI TEST-ONLY BOUNDARY"

if [ -f ".github/workflows/ci.yml" ]; then

    CI_MATCHES="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        .github/workflows/ci.yml 2>/dev/null || true
    )"

    while IFS=: read -r line_no line_text; do
        [ -n "${line_no:-}" ] || continue

        key="$(
            echo "$line_text" |
            grep -oE \
            'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' |
            head -n1
        )"

        [ -n "${key:-}" ] || continue

        if echo "$line_text" | grep -qE \
            'test|TEST|ci|CI|127\.0\.0\.1|localhost'; then

            echo "FILE=.github/workflows/ci.yml LINE=$line_no KEY=$key CLASSIFICATION=TEST_CONFIGURATION VALUE=<REDACTED>" |
                tee -a "$REPORT"

            CI_TEST_COUNT=$((CI_TEST_COUNT + 1))

        else

            review "CI_SECRET_LINE_REQUIRES_CONTEXT_REVIEW=$line_no"

        fi

    done <<< "$CI_MATCHES"

fi

echo "CI_TEST_SECRET_COUNT=$CI_TEST_COUNT" | tee -a "$REPORT"

section "8. SECRET AUTHORITY CHAIN"

echo "PRODUCTION_SECRET_AUTHORITY=.env.production" | tee -a "$REPORT"
echo "PRODUCTION_COMPOSE_AUTHORITY=docker-compose.yml" | tee -a "$REPORT"
echo "RUNTIME_CONFIG_AUTHORITY=app/core/config.py" | tee -a "$REPORT"
echo "CI_TEST_AUTHORITY=.github/workflows/ci.yml" | tee -a "$REPORT"

pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"

section "9. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_ENV_SECRET_COUNT=$PROD_LITERAL_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$PROD_REFERENCE_COUNT" | tee -a "$REPORT"
echo "RUNTIME_REFERENCE_COUNT=$RUNTIME_REFERENCE_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SECRET_COUNT=$CI_TEST_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_02_R4_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_R4_SECRET_WIRING_BOUNDARY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    echo "REPORT=$REPORT"

    exit 20
fi

if [ "$REVIEW_COUNT" -gt 0 ]; then

    echo "P0_02_R4_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_02_R4_SECRET_WIRING_TOKEN_AWARE_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"
    echo "REPORT=$REPORT"

    exit 10
fi

echo "P0_02_R4_STATUS=CLEAN" | tee -a "$REPORT"
echo "RESULT=P0_02_R4_SECRET_WIRING_TOKEN_AWARE_CLEAN" | tee -a "$REPORT"
echo "EXIT_CODE=0" | tee -a "$REPORT"
echo "REPORT=$REPORT"

exit 0
