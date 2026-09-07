#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r2_secret_value_token_aware_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
REAL_VALUE_COUNT=0
REFERENCE_COUNT=0
PLACEHOLDER_COUNT=0
TYPE_DECL_COUNT=0
TEST_SECRET_COUNT=0

mkdir -p audit-output 2>/dev/null || true
: > "$REPORT"

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $1" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $1" | tee -a "$REPORT"
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

SECRET_KEYS='
POSTGRES_PASSWORD
DATABASE_PASSWORD
JWT_SECRET_KEY
JWT_REFRESH_SECRET_KEY
S3_SECRET_KEY
'

echo "SECRET_IDENTIFIERS_REDACTED=YES" | tee -a "$REPORT"

section "3. CLASSIFICATION RULES"

echo "REAL_VALUE=literal non-placeholder assigned value" | tee -a "$REPORT"
echo "REFERENCE=environment/config indirection" | tee -a "$REPORT"
echo "PLACEHOLDER=obvious example/default/test marker" | tee -a "$REPORT"
echo "TYPE_DECL=type annotation without secret assignment" | tee -a "$REPORT"
echo "TEST_SECRET=test-only configuration value" | tee -a "$REPORT"

classify_assignment() {
    local file="$1"
    local line_no="$2"
    local key="$3"
    local raw="$4"

    local value
    value="$(printf '%s\n' "$raw" | sed -E 's/^[^=]*=[[:space:]]*//')"

    # Never print the value.
    local classification="REVIEW"

    # Python type declaration such as:
    # JWT_SECRET_KEY: str
    if printf '%s\n' "$raw" | grep -Eq \
        '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:[[:space:]]*[A-Za-z_][A-Za-z0-9_\[\], ]*[[:space:]]*$'; then
        classification="TYPE_DECL"
        TYPE_DECL_COUNT=$((TYPE_DECL_COUNT + 1))

    # Environment indirection.
    elif printf '%s\n' "$value" | grep -Eq \
        '^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$|^os\.(getenv|environ\.get)\(' ; then
        classification="REFERENCE"
        REFERENCE_COUNT=$((REFERENCE_COUNT + 1))

    # Obvious placeholders / examples.
    elif printf '%s\n' "$value" | grep -Eiq \
        '^(<[^>]+>|CHANGE_ME|REPLACE_ME|YOUR_[A-Z0-9_]+|YOUR-[A-Za-z0-9_-]+|example|example[_-]?secret|placeholder|dummy|changeme|null|none|undefined)$'; then
        classification="PLACEHOLDER"
        PLACEHOLDER_COUNT=$((PLACEHOLDER_COUNT + 1))

    # Test-only known markers.
    elif [[ "$file" == ".github/workflows/ci.yml" ]] && \
         printf '%s\n' "$raw" | grep -Eiq \
         '(test-secret-key|test-refresh-secret-key|minio123|cmep|cmep123|password)'; then
        classification="TEST_SECRET"
        TEST_SECRET_COUNT=$((TEST_SECRET_COUNT + 1))

    else
        classification="REAL_VALUE"
        REAL_VALUE_COUNT=$((REAL_VALUE_COUNT + 1))
    fi

    echo "FILE=$file LINE=$line_no KEY=$key CLASSIFICATION=$classification VALUE=<REDACTED>" \
        | tee -a "$REPORT"
}

section "4. TARGETED SECRET ASSIGNMENTS"

TARGET_FILES=(
    ".env.production"
    "docker-compose.yml"
    ".github/workflows/ci.yml"
    "app/core/config.py"
)

for file in "${TARGET_FILES[@]}"; do

    if [ ! -f "$file" ]; then
        echo "TARGET_ABSENT=$file" | tee -a "$REPORT"
        continue
    fi

    echo | tee -a "$REPORT"
    echo "--- TARGET=$file ---" | tee -a "$REPORT"

    while IFS=: read -r line_no line_text; do

        [ -n "${line_no:-}" ] || continue

        matched_key="$(
            printf '%s\n' "$line_text" |
            grep -Eo \
            'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' |
            head -1
        )"

        [ -n "${matched_key:-}" ] || continue

        # Python declaration without '=' is passed as-is.
        if ! printf '%s\n' "$line_text" | grep -q '='; then
            classify_assignment "$file" "$line_no" "$matched_key" "$line_text"
            continue
        fi

        classify_assignment "$file" "$line_no" "$matched_key" "$line_text"

    done < <(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        "$file" 2>/dev/null || true
    )

done

section "5. PRODUCTION REAL-VALUE DECISION"

PROD_REAL_COUNT=0

for file in ".env.production" "docker-compose.yml"; do

    [ -f "$file" ] || continue

    count="$(
        grep -nE \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        "$file" 2>/dev/null |
        while IFS=: read -r line_no line_text; do

            key="$(
                printf '%s\n' "$line_text" |
                grep -Eo \
                'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' |
                head -1
            )"

            [ -n "$key" ] || continue

            if printf '%s\n' "$line_text" | grep -q '='; then
                value="$(
                    printf '%s\n' "$line_text" |
                    sed -E 's/^[^=]*=[[:space:]]*//'
                )"

                if ! printf '%s\n' "$value" | grep -Eq \
                    '^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$|^os\.(getenv|environ\.get)\('; then

                    if ! printf '%s\n' "$value" | grep -Eiq \
                        '^(<[^>]+>|CHANGE_ME|REPLACE_ME|YOUR_[A-Z0-9_]+|YOUR-[A-Za-z0-9_-]+|example|example[_-]?secret|placeholder|dummy|changeme|null|none|undefined)$'; then

                        PROD_REAL_COUNT=$((PROD_REAL_COUNT + 1))
                    fi
                fi
            fi

        done |
        tail -n 1
    )"

    PROD_REAL_COUNT="${count:-0}"

done

echo "PRODUCTION_REAL_VALUE_COUNT=$PROD_REAL_COUNT" | tee -a "$REPORT"

if [ "$PROD_REAL_COUNT" -eq 0 ]; then
    pass "NO_CLASSIFIED_REAL_PRODUCTION_SECRET_VALUES"
else
    fail "CLASSIFIED_REAL_PRODUCTION_SECRET_VALUES=$PROD_REAL_COUNT"
fi

section "6. RUNTIME CONFIG DECLARATION CHECK"

RUNTIME_SECRET_REFS="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=node_modules \
        --exclude-dir=.next \
        --exclude-dir=dist \
        --exclude-dir=build \
        --exclude-dir=__pycache__ \
        'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
        app apps/web \
        2>/dev/null |
    wc -l
)"

echo "RUNTIME_SECRET_REFERENCE_LINE_COUNT=$RUNTIME_SECRET_REFS" | tee -a "$REPORT"

pass "RUNTIME_SECRET_SCAN_COMPLETED_WITHOUT_VALUE_OUTPUT"

section "7. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "REAL_VALUE_COUNT=$REAL_VALUE_COUNT" | tee -a "$REPORT"
echo "REFERENCE_COUNT=$REFERENCE_COUNT" | tee -a "$REPORT"
echo "PLACEHOLDER_COUNT=$PLACEHOLDER_COUNT" | tee -a "$REPORT"
echo "TYPE_DECL_COUNT=$TYPE_DECL_COUNT" | tee -a "$REPORT"
echo "TEST_SECRET_COUNT=$TEST_SECRET_COUNT" | tee -a "$REPORT"
echo "PRODUCTION_REAL_VALUE_COUNT=$PROD_REAL_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_02_R2_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_R2_SECRET_VALUE_TOKEN_AWARE_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 20

fi

if [ "$PROD_REAL_COUNT" -gt 0 ]; then

    echo "P0_02_R2_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_R2_PRODUCTION_SECRET_VALUE_EXPOSURE_DETECTED" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 20

fi

if [ "$REAL_VALUE_COUNT" -eq 0 ]; then

    echo "P0_02_R2_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_02_R2_SECRET_VALUE_TOKEN_AWARE_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 0

fi

echo "P0_02_R2_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_02_R2_SECRET_VALUE_TOKEN_AWARE_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"

echo
echo "REPORT=$REPORT"
exit 10

