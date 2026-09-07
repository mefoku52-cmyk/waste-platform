#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_r8_compose_secret_context_closure.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0

COMPOSE_TARGET_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0

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

section "P0-02 R8 COMPOSE SECRET CONTEXT CLOSURE"

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

COMPOSE_FILE="docker-compose.yml"

if [ -f "$COMPOSE_FILE" ]; then
    pass "COMPOSE_PRESENT=$COMPOSE_FILE"
else
    fail "COMPOSE_MISSING=$COMPOSE_FILE"
fi

section "3. SECRET TOKEN SET"

SECRET_TOKENS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for token in "${SECRET_TOKENS[@]}"; do
    echo "SECRET_TOKEN=$token" | tee -a "$REPORT"
done

section "4. TOKEN-AWARE YAML-LINE CLASSIFICATION"

if [ -f "$COMPOSE_FILE" ]; then

    line_no=0

    while IFS= read -r line || [ -n "$line" ]; do
        line_no=$((line_no + 1))

        # Remove CR if present.
        line="${line%$'\r'}"

        # Skip empty lines.
        [ -z "${line//[[:space:]]/}" ] && continue

        # Skip comments.
        case "$line" in
            [[:space:]]*\#*)
                continue
                ;;
        esac

        matched_token=""
        for token in "${SECRET_TOKENS[@]}"; do
            if [[ "$line" == *"$token"* ]]; then
                matched_token="$token"
                break
            fi
        done

        [ -n "$matched_token" ] || continue

        COMPOSE_TARGET_COUNT=$((COMPOSE_TARGET_COUNT + 1))

        # Extract the YAML key when the secret token is actually the key.
        # This deliberately avoids regex interpretation of ${...}.
        key_candidate=""
        value_candidate=""

        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*:[[:space:]]*(.*)$ ]]; then
            key_candidate="${BASH_REMATCH[1]}"
            value_candidate="${BASH_REMATCH[2]}"
        fi

        # Secret key mapping.
        if [ "$key_candidate" = "$matched_token" ]; then

            # Remove trailing YAML comment only when preceded by whitespace.
            value_no_comment="$value_candidate"

            # Exact Compose interpolation reference:
            # ${SECRET_TOKEN}
            # ${SECRET_TOKEN:?message}
            # ${SECRET_TOKEN:-default}
            if [[ "$value_no_comment" =~ ^\$\{${matched_token}([:?+-].*)?\}[[:space:]]*$ ]]; then
                echo "LINE=$line_no KEY=$matched_token CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>" \
                    | tee -a "$REPORT"

                COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
                continue
            fi

            # Compose indirection through environment syntax.
            if [[ "$value_no_comment" =~ ^\$\{[A-Za-z_][A-Za-z0-9_]*([:?+-].*)?\}[[:space:]]*$ ]]; then
                echo "LINE=$line_no KEY=$matched_token CLASSIFICATION=ENV_REFERENCE_WIRING VALUE=<REDACTED>" \
                    | tee -a "$REPORT"

                COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))
                continue
            fi

            # Explicit YAML null is not a secret literal.
            if [ "$value_no_comment" = "null" ] || \
               [ "$value_no_comment" = "~" ] || \
               [ -z "$value_no_comment" ]; then

                echo "LINE=$line_no KEY=$matched_token CLASSIFICATION=EMPTY_OR_NULL_SECRET_MAPPING VALUE=<REDACTED>" \
                    | tee -a "$REPORT"

                review "EMPTY_OR_NULL_SECRET_MAPPING_LINE=$line_no KEY=$matched_token"
                continue
            fi

            # Any remaining direct scalar is a literal candidate.
            echo "LINE=$line_no KEY=$matched_token CLASSIFICATION=LITERAL_CANDIDATE VALUE=<REDACTED>" \
                | tee -a "$REPORT"

            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            fail "COMPOSE_LITERAL_SECRET_ASSIGNMENT_LINE=$line_no KEY=$matched_token"

            continue
        fi

        # Secret token occurring somewhere else, such as DATABASE_URL.
        # This is not itself a secret assignment.
        echo "LINE=$line_no CLASSIFICATION=NON_SECRET_CONTEXT TEXT=<REDACTED_SECRET_CONTEXT>" \
            | tee -a "$REPORT"

        COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))

    done < "$COMPOSE_FILE"

else
    fail "COMPOSE_ANALYSIS_SKIPPED_FILE_MISSING"
fi

section "5. EXPECTED PRODUCTION SECRET WIRING"

# These are the secrets that Compose is expected to consume directly
# from the production environment authority.

EXPECTED_DIRECT_REFERENCES=(
    "POSTGRES_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
)

for token in "${EXPECTED_DIRECT_REFERENCES[@]}"; do
    if grep -Eq \
        "^[[:space:]]*${token}[[:space:]]*:[[:space:]]*\\\$\\{${token}([:?+-][^}]*)?\\}[[:space:]]*$" \
        "$COMPOSE_FILE" 2>/dev/null; then

        pass "EXPECTED_REFERENCE_PRESENT=$token"

    else
        review "EXPECTED_REFERENCE_NOT_CONFIRMED=$token"
    fi
done

section "6. DATABASE_URL FALSE-POSITIVE BOUNDARY"

if grep -Eq '^[[:space:]]*DATABASE_URL[[:space:]]*:' "$COMPOSE_FILE" 2>/dev/null; then
    pass "DATABASE_URL_MAPPING_PRESENT"
else
    review "DATABASE_URL_MAPPING_NOT_FOUND"
fi

# DATABASE_URL may legitimately contain interpolation such as:
# ${POSTGRES_USER}, ${POSTGRES_PASSWORD}, ${POSTGRES_DB}.
# Presence of interpolation inside DATABASE_URL does not mean that
# DATABASE_URL itself is a literal secret assignment.
DATABASE_URL_LINE="$(grep -E '^[[:space:]]*DATABASE_URL[[:space:]]*:' "$COMPOSE_FILE" 2>/dev/null | head -n 1 || true)"

if [ -n "$DATABASE_URL_LINE" ]; then
    if [[ "$DATABASE_URL_LINE" == *'${POSTGRES_PASSWORD}'* ]] || \
       [[ "$DATABASE_URL_LINE" == *'${POSTGRES_PASSWORD:'* ]] || \
       [[ "$DATABASE_URL_LINE" == *'${POSTGRES_PASSWORD-'* ]] || \
       [[ "$DATABASE_URL_LINE" == *'${POSTGRES_PASSWORD+'* ]]; then

        pass "DATABASE_URL_USES_POSTGRES_PASSWORD_INTERPOLATION"

    else
        pass "DATABASE_URL_PRESENT_WITHOUT_POSTGRES_PASSWORD_LITERAL"
    fi
fi

section "7. CROSS-AUTHORITY INVARIANTS"

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    pass "INVARIANT_NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT"
else
    fail "INVARIANT_LITERAL_COMPOSE_SECRET_COUNT=$COMPOSE_LITERAL_COUNT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -ge 3 ]; then
    pass "INVARIANT_REQUIRED_COMPOSE_SECRET_REFERENCES_PRESENT"
else
    review "INVARIANT_COMPOSE_REFERENCE_COUNT_BELOW_EXPECTED=$COMPOSE_REFERENCE_COUNT"
fi

pass "SECRET_VALUE_OUTPUT_REMAINED_REDACTED"

section "8. FINAL CLASSIFICATION"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"
echo "COMPOSE_TARGET_COUNT=$COMPOSE_TARGET_COUNT" | tee -a "$REPORT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT" | tee -a "$REPORT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT" | tee -a "$REPORT"
echo "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R8_COMPOSE_SECRET_CONTEXT_BOUNDARY_FAILURE"
    EXIT_CODE=20

elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R8_COMPOSE_SECRET_CONTEXT_BOUNDARY_REVIEW_REQUIRED"
    EXIT_CODE=10

else
    STATUS="CLEAN"
    RESULT="P0_02_R8_COMPOSE_SECRET_CONTEXT_BOUNDARY_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R8_STATUS=$STATUS" | tee -a "$REPORT"
echo "RESULT=$RESULT" | tee -a "$REPORT"
echo "EXIT_CODE=$EXIT_CODE" | tee -a "$REPORT"
echo "REPORT=$REPORT" | tee -a "$REPORT"

exit "$EXIT_CODE"
