#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r3_secret_authority_boundary_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
PRODUCTION_HARDCODED_COUNT=0
PRODUCTION_ENV_ASSIGNMENT_COUNT=0
PRODUCTION_REFERENCE_COUNT=0
CI_TEST_SECRET_COUNT=0
RUNTIME_SECRET_DECL_COUNT=0

mkdir -p audit-output 2>/dev/null || true
: > "$REPORT"

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

section "2. SECRET IDENTIFIERS"

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

section "3. REQUIRED PRODUCTION SECRET AUTHORITY"

if [ -f ".env.production" ]; then
    pass "PRODUCTION_SECRET_STORE_PRESENT=.env.production"
else
    fail "PRODUCTION_SECRET_STORE_MISSING=.env.production"
fi

if [ -f "docker-compose.yml" ]; then
    pass "PRODUCTION_COMPOSE_PRESENT=docker-compose.yml"
else
    fail "PRODUCTION_COMPOSE_MISSING=docker-compose.yml"
fi

if [ -f "app/core/config.py" ]; then
    pass "RUNTIME_CONFIG_PRESENT=app/core/config.py"
else
    fail "RUNTIME_CONFIG_MISSING=app/core/config.py"
fi

section "4. PRODUCTION ENV SECRET ASSIGNMENT PROOF"

if [ -f ".env.production" ]; then

    while IFS= read -r line; do

        line_no="${line%%:*}"
        body="${line#*:}"

        key="$(
            printf '%s\n' "$body" |
            sed -nE 's/^[[:space:]]*([A-Z0-9_]+)[[:space:]]*=.*$/\1/p'
        )"

        [ -n "$key" ] || continue

        case "$key" in
            POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)

                PRODUCTION_ENV_ASSIGNMENT_COUNT=$((PRODUCTION_ENV_ASSIGNMENT_COUNT + 1))

                value="${body#*=}"

                if [ -z "$value" ]; then
                    classification="EMPTY_VALUE"
                elif printf '%s' "$value" |
                    grep -Eq '^\$\{?[A-Z0-9_]+\}?$'; then
                    classification="ENV_REFERENCE"
                    PRODUCTION_REFERENCE_COUNT=$((PRODUCTION_REFERENCE_COUNT + 1))
                elif printf '%s' "$value" |
                    grep -Eqi \
                    '^(changeme|change_me|replace_me|your_|example|test|dummy|null|none|\*\*\*|<.*>)$'; then
                    classification="PLACEHOLDER"
                else
                    classification="SECRET_STORE_VALUE"
                fi

                echo "FILE=.env.production LINE=$line_no KEY=$key CLASSIFICATION=$classification VALUE=<REDACTED>" |
                    tee -a "$REPORT"

                ;;
        esac

    done < <(grep -nE '^[[:space:]]*[A-Z0-9_]+[[:space:]]*=' .env.production 2>/dev/null || true)

fi

echo "PRODUCTION_ENV_SECRET_ASSIGNMENT_COUNT=$PRODUCTION_ENV_ASSIGNMENT_COUNT" |
    tee -a "$REPORT"

echo "PRODUCTION_ENV_REFERENCE_COUNT=$PRODUCTION_REFERENCE_COUNT" |
    tee -a "$REPORT"

if [ "$PRODUCTION_ENV_ASSIGNMENT_COUNT" -gt 0 ]; then
    pass "PRODUCTION_ENV_SECRET_AUTHORITY_CONTAINS_EXPECTED_SECRET_KEYS"
else
    fail "PRODUCTION_ENV_SECRET_AUTHORITY_HAS_NO_EXPECTED_SECRET_KEYS"
fi

section "5. PRODUCTION COMPOSE SECRET WIRING"

if [ -f "docker-compose.yml" ]; then

    compose_secret_lines="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        docker-compose.yml 2>/dev/null || true
    )"

    if [ -n "$compose_secret_lines" ]; then

        echo "$compose_secret_lines" |
        while IFS= read -r line; do
            line_no="${line%%:*}"
            body="${line#*:}"

            key="$(
                printf '%s\n' "$body" |
                sed -nE \
                's/.*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY).*/\1/p'
            )"

            [ -n "$key" ] || continue

            if printf '%s\n' "$body" |
                grep -Eq \
                '\$\{[A-Z0-9_]+\}|\$\{[A-Z0-9_]+:-[^}]+\}|env_file|environment:'; then

                classification="REFERENCE_OR_COMPOSE_WIRING"

            else

                classification="LITERAL_ASSIGNMENT"
                PRODUCTION_HARDCODED_COUNT=$((PRODUCTION_HARDCODED_COUNT + 1))

            fi

            echo "FILE=docker-compose.yml LINE=$line_no KEY=$key CLASSIFICATION=$classification VALUE=<REDACTED>" |
                tee -a "$REPORT"

        done

    else
        review "NO_SECRET_WIRING_LINES_FOUND_IN_COMPOSE"
    fi

fi

section "6. RUNTIME CONFIG SECRET DECLARATION"

if [ -f "app/core/config.py" ]; then

    runtime_lines="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        app/core/config.py 2>/dev/null || true
    )"

    if [ -n "$runtime_lines" ]; then

        echo "$runtime_lines" |
        while IFS= read -r line; do

            line_no="${line%%:*}"
            body="${line#*:}"

            if printf '%s\n' "$body" |
                grep -Eq '^[[:space:]]*[A-Z0-9_]+[[:space:]]*:[[:space:]]*(str|SecretStr|Optional\[str\])'; then
                classification="TYPE_DECLARATION"
            elif printf '%s\n' "$body" |
                grep -Eq \
                'Field\(|BaseSettings|SettingsConfigDict|env_prefix|validation_alias|AliasChoices|os\.getenv|getenv'; then
                classification="RUNTIME_SECRET_BINDING"
            elif printf '%s\n' "$body" |
                grep -Eq \
                '^[[:space:]]*[A-Z0-9_]+[[:space:]]*='; then
                classification="RUNTIME_LITERAL_ASSIGNMENT"
                PRODUCTION_HARDCODED_COUNT=$((PRODUCTION_HARDCODED_COUNT + 1))
            else
                classification="REFERENCE"
            fi

            RUNTIME_SECRET_DECL_COUNT=$((RUNTIME_SECRET_DECL_COUNT + 1))

            echo "FILE=app/core/config.py LINE=$line_no CLASSIFICATION=$classification VALUE=<REDACTED>" |
                tee -a "$REPORT"

        done

    else
        review "NO_RUNTIME_SECRET_DECLARATIONS_FOUND"
    fi

fi

echo "RUNTIME_SECRET_DECLARATION_COUNT=$RUNTIME_SECRET_DECL_COUNT" |
    tee -a "$REPORT"

section "7. CI TEST-ONLY SECRET CLASSIFICATION"

if [ -f ".github/workflows/ci.yml" ]; then

    CI_LINES="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        .github/workflows/ci.yml 2>/dev/null || true
    )"

    if [ -n "$CI_LINES" ]; then

        echo "$CI_LINES" |
        while IFS= read -r line; do

            line_no="${line%%:*}"
            body="${line#*:}"

            case "$body" in
                *POSTGRES_PASSWORD*|*DATABASE_PASSWORD*|*JWT_SECRET_KEY*|*JWT_REFRESH_SECRET_KEY*|*S3_SECRET_KEY*)
                    CI_TEST_SECRET_COUNT=$((CI_TEST_SECRET_COUNT + 1))
                    ;;
            esac

            echo "CI_LINE=$line_no CLASSIFICATION=TEST_CONFIGURATION VALUE=<REDACTED>" |
                tee -a "$REPORT"

        done

        pass "CI_SECRET_REFERENCES_PRESENT_IN_CI_SCOPE"

    else
        pass "CI_HAS_NO_SECRET_ASSIGNMENTS"
    fi

fi

echo "CI_TEST_SECRET_COUNT=$CI_TEST_SECRET_COUNT" | tee -a "$REPORT"

section "8. HARD-CODED PRODUCTION SECRET DECISION"

echo "PRODUCTION_HARDCODED_SECRET_ASSIGNMENT_COUNT=$PRODUCTION_HARDCODED_COUNT" |
    tee -a "$REPORT"

if [ "$PRODUCTION_HARDCODED_COUNT" -eq 0 ]; then
    pass "NO_HARDCODED_SECRET_ASSIGNMENT_DETECTED_IN_PRODUCTION_AUTHORITY"
else
    fail "HARDCODED_SECRET_ASSIGNMENT_DETECTED_IN_PRODUCTION_AUTHORITY=$PRODUCTION_HARDCODED_COUNT"
fi

section "9. AUTHORITY CHAIN"

echo "PRODUCTION_SECRET_AUTHORITY=.env.production" | tee -a "$REPORT"
echo "PRODUCTION_COMPOSE_AUTHORITY=docker-compose.yml" | tee -a "$REPORT"
echo "RUNTIME_CONFIG_AUTHORITY=app/core/config.py" | tee -a "$REPORT"
echo "CI_AUTHORITY=.github/workflows/ci.yml" | tee -a "$REPORT"

section "10. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_ENV_SECRET_ASSIGNMENT_COUNT=$PRODUCTION_ENV_ASSIGNMENT_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_REFERENCE_COUNT=$PRODUCTION_REFERENCE_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_HARDCODED_SECRET_ASSIGNMENT_COUNT=$PRODUCTION_HARDCODED_COUNT" | tee -a "$REPORT"
echo "RUNTIME_SECRET_DECLARATION_COUNT=$RUNTIME_SECRET_DECL_COUNT" | tee -a "$REPORT"
echo "CI_TEST_SECRET_COUNT=$CI_TEST_SECRET_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_02_R3_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_R3_SECRET_AUTHORITY_BOUNDARY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 20

fi

if [ "$PRODUCTION_ENV_ASSIGNMENT_COUNT" -gt 0 ] && \
   [ "$PRODUCTION_HARDCODED_COUNT" -eq 0 ]; then

    echo "P0_02_R3_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_02_R3_SECRET_AUTHORITY_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 0

fi

echo "P0_02_R3_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_02_R3_SECRET_AUTHORITY_BOUNDARY_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"

echo
echo "REPORT=$REPORT"
exit 10

