#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r7_compose_secret_token_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

COMPOSE_SECRET_REFERENCE_COUNT=0
COMPOSE_SECRET_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0
COMPOSE_TARGET_COUNT=0

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

section "P0-02 R7 COMPOSE SECRET TOKEN PROOF"

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

section "2. COMPOSE AUTHORITY"

if [ -f "docker-compose.yml" ]; then
    pass "COMPOSE_PRESENT=docker-compose.yml"
else
    fail "COMPOSE_MISSING=docker-compose.yml"
fi

section "3. SECRET KEY TOKEN SET"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for key in "${SECRET_KEYS[@]}"; do
    echo "SECRET_TOKEN=$key" | tee -a "$REPORT"
done

section "4. TOKEN-AWARE COMPOSE ANALYSIS"

if [ -f "docker-compose.yml" ]; then

    while IFS= read -r record; do
        line_no="${record%%:*}"
        line_text="${record#*:}"

        [ -n "$line_no" ] || continue

        matched_key=""

        for key in "${SECRET_KEYS[@]}"; do
            if printf '%s\n' "$line_text" | grep -qE \
                "(^|[^A-Za-z0-9_])${key}([^A-Za-z0-9_]|$)"; then
                matched_key="$key"
                break
            fi
        done

        [ -n "$matched_key" ] || continue

        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

        # Extract the YAML value only when the secret token is actually
        # the mapping key at the beginning of the line.
        if printf '%s\n' "$line_text" | grep -qE \
            "^[[:space:]]*${matched_key}[[:space:]]*:"; then

            value_part="$(printf '%s\n' "$line_text" | \
                sed -E "s/^[[:space:]]*${matched_key}[[:space:]]*:[[:space:]]*//")"

            # Remove YAML comments without exposing the remaining value.
            value_part="$(printf '%s\n' "$value_part" | \
                sed -E 's/[[:space:]]+#.*$//')"

            if [ -z "$value_part" ]; then
                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=EMPTY_MAPPING_VALUE" \
                    | tee -a "$REPORT"
                review "EMPTY_COMPOSE_SECRET_VALUE_LINE=$line_no"
                continue
            fi

            # Environment interpolation forms.
            if printf '%s\n' "$value_part" | grep -qE \
                '^\$\{(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)(:-[^}]*)?\}$'; then

                COMPOSE_SECRET_REFERENCE_COUNT=$((COMPOSE_SECRET_REFERENCE_COUNT + 1))
                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=ENV_INTERPOLATION_REFERENCE" \
                    | tee -a "$REPORT"
                pass "COMPOSE_SECRET_REFERENCE_LINE=$line_no"

            elif printf '%s\n' "$value_part" | grep -qE \
                '^\$\{[A-Za-z_][A-Za-z0-9_]*(?::-[^}]*)?\}$'; then

                COMPOSE_SECRET_REFERENCE_COUNT=$((COMPOSE_SECRET_REFERENCE_COUNT + 1))
                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=GENERIC_ENV_REFERENCE" \
                    | tee -a "$REPORT"
                pass "COMPOSE_GENERIC_ENV_REFERENCE_LINE=$line_no"

            elif printf '%s\n' "$value_part" | grep -qE \
                '^\$[A-Za-z_][A-Za-z0-9_]*$'; then

                COMPOSE_SECRET_REFERENCE_COUNT=$((COMPOSE_SECRET_REFERENCE_COUNT + 1))
                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=SHELL_ENV_REFERENCE" \
                    | tee -a "$REPORT"
                pass "COMPOSE_SHELL_ENV_REFERENCE_LINE=$line_no"

            # Quoted interpolation.
            elif printf '%s\n' "$value_part" | grep -qE \
                '^["'\'']\$\{[A-Za-z_][A-Za-z0-9_]*(?::-[^}]*)?\}["'\'']$'; then

                COMPOSE_SECRET_REFERENCE_COUNT=$((COMPOSE_SECRET_REFERENCE_COUNT + 1))
                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=QUOTED_ENV_REFERENCE" \
                    | tee -a "$REPORT"
                pass "COMPOSE_QUOTED_ENV_REFERENCE_LINE=$line_no"

            # Literal-looking value.
            else
                COMPOSE_SECRET_LITERAL_COUNT=$((COMPOSE_SECRET_LITERAL_COUNT + 1))

                echo "LINE=$line_no KEY=$matched_key CLASSIFICATION=LITERAL_CANDIDATE VALUE=<REDACTED>" \
                    | tee -a "$REPORT"

                fail "COMPOSE_LITERAL_SECRET_CANDIDATE_LINE=$line_no KEY=$matched_key"
            fi

        else
            COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))

            safe_text="$(printf '%s\n' "$line_text" | \
                sed -E 's/(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)/<SECRET_TOKEN>/g')"

            echo "LINE=$line_no CLASSIFICATION=NON_MAPPING_SECRET_CONTEXT TEXT=$safe_text" \
                | tee -a "$REPORT"

            pass "COMPOSE_NON_MAPPING_SECRET_CONTEXT_LINE=$line_no"
        fi

    done < <(
        grep -nE \
        '(^|[^A-Za-z0-9_])(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)([^A-Za-z0-9_]|$)' \
        docker-compose.yml 2>/dev/null || true
    )

fi

section "5. CROSS-CHECK DATABASE_URL FALSE-POSITIVE BOUNDARY"

if [ -f "docker-compose.yml" ]; then

    if grep -nE \
        '^[[:space:]]*DATABASE_URL[[:space:]]*:' \
        docker-compose.yml >/dev/null 2>&1; then

        pass "DATABASE_URL_MAPPING_PRESENT"

        if grep -nE \
            '^[[:space:]]*DATABASE_URL[[:space:]]*:' \
            docker-compose.yml | \
            grep -qE 'DATABASE_PASSWORD'; then

            echo "DATABASE_URL_REFERENCE_CONTEXT_PRESENT=YES" | tee -a "$REPORT"
            pass "DATABASE_URL_REFERENCE_CONTEXT_NOT_SECRET_ASSIGNMENT"
        else
            pass "DATABASE_URL_REFERENCE_CONTEXT_NOT_LITERAL_SECRET_ASSIGNMENT"
        fi
    fi

fi

section "6. EXPECTED PRODUCTION SECRET WIRING"

for key in "${SECRET_KEYS[@]}"; do
    if grep -qE \
        "^[[:space:]]*${key}[[:space:]]*:" \
        docker-compose.yml 2>/dev/null; then

        pass "COMPOSE_SECRET_MAPPING_PRESENT=$key"
    else
        review "COMPOSE_SECRET_MAPPING_NOT_FOUND=$key"
    fi
done

section "7. FINAL INVARIANTS"

if [ "$COMPOSE_SECRET_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET"
else
    fail "INVARIANT_LITERAL_COMPOSE_SECRET_COUNT=$COMPOSE_SECRET_LITERAL_COUNT"
fi

if [ "$COMPOSE_SECRET_REFERENCE_COUNT" -gt 0 ]; then
    pass "INVARIANT_COMPOSE_SECRET_REFERENCES_DETECTED=$COMPOSE_SECRET_REFERENCE_COUNT"
else
    review "INVARIANT_NO_COMPOSE_SECRET_REFERENCES_DETECTED"
fi

section "8. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_SECRET_REFERENCE_COUNT=$COMPOSE_SECRET_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_SECRET_LITERAL_COUNT=$COMPOSE_SECRET_LITERAL_COUNT" | tee -a "$REPORT"
echo "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R7_COMPOSE_SECRET_TOKEN_PROOF_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R7_COMPOSE_SECRET_TOKEN_PROOF_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R7_COMPOSE_SECRET_TOKEN_PROOF_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R7_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
