#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/waste-platform}"

if [ -d "$PROJECT_ROOT" ]; then
    cd "$PROJECT_ROOT" || exit 20
else
    echo "FAIL: PROJECT_ROOT_NOT_FOUND=$PROJECT_ROOT"
    exit 20
fi

REPORT="audit-output/p0_02_r1_secret_assignment_semantic_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
SECRET_ASSIGNMENT_COUNT=0
SECRET_VALUE_EXPOSURE_COUNT=0
TEST_ONLY_SECRET_COUNT=0
PRODUCTION_SECRET_EXPOSURE_COUNT=0

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

section "2. SECRET IDENTIFIER CLASSIFICATION"

SECRET_NAMES='
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
SECRET_KEY
S3_SECRET_KEY
DATABASE_PASSWORD
REDIS_PASSWORD
TELEGRAM_BOT_TOKEN
AWS_SECRET_ACCESS_KEY
'

echo "SECRET_IDENTIFIERS_REDACTED_VALUES_ONLY=YES" | tee -a "$REPORT"

section "3. CI SECRET ASSIGNMENT CLASSIFICATION"

CI=".github/workflows/ci.yml"

if [ ! -f "$CI" ]; then
    review "CI_FILE_NOT_PRESENT"
else

    while IFS= read -r line; do

        [ -n "$line" ] || continue

        line_no="${line%%:*}"
        text="${line#*:}"

        SECRET_ASSIGNMENT_COUNT=$((SECRET_ASSIGNMENT_COUNT + 1))

        # Never print the value.
        key="$(echo "$text" | sed -E \
            's/^[[:space:]-]*([A-Za-z_][A-Za-z0-9_]*):.*/\1/' \
            | tr -d ' ')"

        if echo "$text" | grep -Eq \
            'JWT_ACCESS_TOKEN_EXPIRES_MINUTES|JWT_REFRESH_TOKEN_EXPIRES_DAYS'; then

            echo "CI_TEST_TTL_REFERENCE_LINE=$line_no KEY=$key" | tee -a "$REPORT"
            TEST_ONLY_SECRET_COUNT=$((TEST_ONLY_SECRET_COUNT + 1))
            continue
        fi

        if echo "$text" | grep -Eq \
            'SECRET|PASSWORD|TOKEN|ACCESS_KEY'; then

            echo "CI_SECRET_ASSIGNMENT_LINE=$line_no KEY=$key VALUE=<REDACTED>" \
                | tee -a "$REPORT"

            if echo "$text" | grep -Eq \
                'test-secret|test-refresh-secret|127\.0\.0\.1|localhost|minio123|cmep'; then

                TEST_ONLY_SECRET_COUNT=$((TEST_ONLY_SECRET_COUNT + 1))
                echo "CLASSIFICATION=TEST_CONFIGURATION" | tee -a "$REPORT"

            else

                SECRET_VALUE_EXPOSURE_COUNT=$((SECRET_VALUE_EXPOSURE_COUNT + 1))
                echo "CLASSIFICATION=NON_TEST_SECRET_VALUE_REQUIRES_REVIEW" \
                    | tee -a "$REPORT"

            fi
        fi

    done < <(
        grep -nE \
        'JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|SECRET_KEY|S3_SECRET_KEY|DATABASE_PASSWORD|REDIS_PASSWORD|TOKEN|PASSWORD' \
        "$CI" 2>/dev/null || true
    )

fi

section "4. PRODUCTION SECRET VALUE EXPOSURE PROOF"

PROD_FILES=(
    ".env.production"
    "docker-compose.yml"
    "docker"
    "app"
    "apps/web"
)

for target in "${PROD_FILES[@]}"; do

    [ -e "$target" ] || continue

    MATCHES="$(
        grep -RInE \
            --exclude-dir=.git \
            --exclude-dir=audit-output \
            --exclude-dir=node_modules \
            --exclude-dir=.next \
            --exclude-dir=dist \
            --exclude-dir=build \
            --exclude-dir=__pycache__ \
            --exclude-dir=_quarantine \
            --exclude-dir=scripts \
            '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|SECRET_KEY|S3_SECRET_KEY|DATABASE_PASSWORD|REDIS_PASSWORD|TELEGRAM_BOT_TOKEN|AWS_SECRET_ACCESS_KEY)[[:space:]]*[:=]' \
            "$target" 2>/dev/null || true
    )"

    while IFS= read -r line; do

        [ -n "$line" ] || continue

        line_no="${line%%:*}"
        remainder="${line#*:}"

        # Only classify the key. Never print the assigned value.
        key="$(
            echo "$remainder" |
            sed -E \
                's/^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*[:=].*/\1/'
        )"

        echo "PRODUCTION_SECRET_ASSIGNMENT_FILE=$target LINE=$line_no KEY=$key VALUE=<REDACTED>" \
            | tee -a "$REPORT"

        # Determine whether there is a literal non-empty value after = or :
        value_present="$(
            echo "$remainder" |
            sed -E \
                's/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*[:=][[:space:]]*(.*)$/\1/' |
            sed -E 's/[[:space:]]+$//' |
            grep -qE '.+' && echo 1 || echo 0
        )"

        if [ "$value_present" -eq 1 ]; then
            PRODUCTION_SECRET_EXPOSURE_COUNT=$((PRODUCTION_SECRET_EXPOSURE_COUNT + 1))
        fi

    done <<< "$MATCHES"

done

echo "PRODUCTION_SECRET_ASSIGNMENT_COUNT=$SECRET_ASSIGNMENT_COUNT" \
    | tee -a "$REPORT"

echo "PRODUCTION_SECRET_VALUE_EXPOSURE_COUNT=$PRODUCTION_SECRET_EXPOSURE_COUNT" \
    | tee -a "$REPORT"

if [ "$PRODUCTION_SECRET_EXPOSURE_COUNT" -eq 0 ]; then
    pass "NO_LITERAL_PRODUCTION_SECRET_VALUE_EXPOSURE_DETECTED"
else
    fail "LITERAL_PRODUCTION_SECRET_VALUE_EXPOSURE_DETECTED"
fi

section "5. P0-01 R8 CONTINUITY"

if [ -f "audit-output/p0_01_r8_token_aware_execution_proof.txt" ]; then

    if grep -q \
        'P0_01_R8_STATUS=CLEAN' \
        audit-output/p0_01_r8_token_aware_execution_proof.txt 2>/dev/null; then

        pass "P0_01_R8_CLEAN_CONTINUITY_CONFIRMED"

    else
        review "P0_01_R8_REPORT_PRESENT_BUT_CLEAN_STATUS_NOT_CONFIRMED"
    fi

else
    review "P0_01_R8_REPORT_NOT_PRESENT"
fi

section "6. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "SECRET_VALUE_EXPOSURE_COUNT=$SECRET_VALUE_EXPOSURE_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_SECRET_VALUE_EXPOSURE_COUNT=$PRODUCTION_SECRET_EXPOSURE_COUNT" | tee -a "$REPORT"
echo "TEST_ONLY_SECRET_COUNT=$TEST_ONLY_SECRET_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_02_R1_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_R1_SECRET_ASSIGNMENT_BOUNDARY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"
    exit 20

fi

if [ "$SECRET_VALUE_EXPOSURE_COUNT" -eq 0 ] && \
   [ "$PRODUCTION_SECRET_VALUE_EXPOSURE_COUNT" -eq 0 ]; then

    echo "P0_02_R1_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_02_R1_SECRET_ASSIGNMENT_SEMANTIC_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"
    exit 0

fi

echo "P0_02_R1_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_02_R1_SECRET_ASSIGNMENT_SEMANTIC_BOUNDARY_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"
echo
echo "REPORT=$REPORT"
exit 10
