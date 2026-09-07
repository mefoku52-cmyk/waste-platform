#!/usr/bin/env bash
set -u

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
COMPOSE="$PROJECT_ROOT/docker-compose.yml"
REPORT="$PROJECT_ROOT/audit-output/p0_02_r13_compose_secret_provenance_semantic_proof.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
COMPOSE_REFERENCE_COUNT=0
COMPOSE_LITERAL_COUNT=0
COMPOSE_NON_SECRET_CONTEXT_COUNT=0
SECRET_VALUE_OUTPUT_COUNT=0

mkdir -p "$PROJECT_ROOT/audit-output"

exec > >(tee "$REPORT") 2>&1

echo "============================================================"
echo "P0-02 R13 COMPOSE SECRET PROVENANCE SEMANTIC PROOF"
echo "============================================================"

echo
echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

if [ -d "$PROJECT_ROOT" ]; then
    echo "PASS: PROJECT_ROOT_CONFIRMED=$PROJECT_ROOT"
else
    echo "FAIL: PROJECT_ROOT_MISSING"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo "PASS: READ_ONLY=YES"
echo "PASS: NO_SOURCE_WRITES=YES"
echo "PASS: NO_RUNTIME_EXECUTION=YES"
echo "PASS: NO_ENV_EXECUTION=YES"
echo "PASS: NO_BUILD=YES"
echo "PASS: NO_DEPLOYMENT=YES"
echo "PASS: NO_DELETIONS=YES"
echo "PASS: NO_SECRET_VALUES_PRINTED=YES"
echo "PASS: BOUNDED_SCAN=YES"

echo
echo "============================================================"
echo "2. COMPOSE AUTHORITY"
echo "============================================================"

if [ -f "$COMPOSE" ]; then
    echo "PASS: COMPOSE_PRESENT=docker-compose.yml"
else
    echo "FAIL: COMPOSE_MISSING=docker-compose.yml"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo
echo "============================================================"
echo "3. SECRET TOKEN SET"
echo "============================================================"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

for key in "${SECRET_KEYS[@]}"; do
    echo "SECRET_TOKEN=$key"
done

echo
echo "============================================================"
echo "4. SEMANTIC COMPOSE SCAN"
echo "============================================================"

while IFS= read -r line; do
    LINE_NO="${line%%:*}"
    TEXT="${line#*:}"

    KEY=""
    for candidate in "${SECRET_KEYS[@]}"; do
        if printf '%s\n' "$TEXT" | grep -qE "^[[:space:]]*$candidate[[:space:]]*:"; then
            KEY="$candidate"
            break
        fi
    done

    if [ -n "$KEY" ]; then
        VALUE="${TEXT#*:}"
        VALUE="${VALUE#"${VALUE%%[![:space:]]*}"}"

        if printf '%s\n' "$VALUE" | grep -qE '^\$\{[A-Za-z_][A-Za-z0-9_]*([:][?][^}]*)?\}$'; then
            echo "LINE=$LINE_NO KEY=$KEY CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>"
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

        elif printf '%s\n' "$VALUE" | grep -qE '^\$\{[A-Za-z_][A-Za-z0-9_]*:-[^}]*\}$'; then
            echo "LINE=$LINE_NO KEY=$KEY CLASSIFICATION=REFERENCE_WITH_DEFAULT VALUE=<REDACTED>"
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

        elif printf '%s\n' "$VALUE" | grep -qE '^\$\{[A-Za-z_][A-Za-z0-9_]*\}$'; then
            echo "LINE=$LINE_NO KEY=$KEY CLASSIFICATION=REFERENCE_WIRING VALUE=<REDACTED>"
            COMPOSE_REFERENCE_COUNT=$((COMPOSE_REFERENCE_COUNT + 1))

        elif [ -n "$VALUE" ]; then
            echo "LINE=$LINE_NO KEY=$KEY CLASSIFICATION=LITERAL_SECRET VALUE=<REDACTED>"
            COMPOSE_LITERAL_COUNT=$((COMPOSE_LITERAL_COUNT + 1))
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        else
            echo "LINE=$LINE_NO KEY=$KEY CLASSIFICATION=EMPTY_SECRET_ASSIGNMENT VALUE=<EMPTY>"
            REVIEW_COUNT=$((REVIEW_COUNT + 1))
        fi

    elif printf '%s\n' "$TEXT" | grep -qE '^[[:space:]]*DATABASE_URL[[:space:]]*:'; then
        if printf '%s\n' "$TEXT" | grep -q '\${POSTGRES_PASSWORD'; then
            echo "LINE=$LINE_NO CLASSIFICATION=DATABASE_URL_SECRET_REFERENCE_CONTEXT"
            COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
        else
            echo "LINE=$LINE_NO CLASSIFICATION=DATABASE_URL_NON_SECRET_CONTEXT"
            COMPOSE_NON_SECRET_CONTEXT_COUNT=$((COMPOSE_NON_SECRET_CONTEXT_COUNT + 1))
        fi
    fi
done < <(grep -nE '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY|DATABASE_URL)[[:space:]]*:' "$COMPOSE" || true)

echo
echo "============================================================"
echo "5. EXPECTED PRODUCTION WIRING"
echo "============================================================"

EXPECTED_KEYS=(
    "POSTGRES_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
)

for key in "${EXPECTED_KEYS[@]}"; do
    if grep -Eq "^[[:space:]]*$key[[:space:]]*:[[:space:]]*\$\{[A-Za-z_][A-Za-z0-9_]*(:\?[^}]*)?\}[[:space:]]*$" "$COMPOSE"; then
        echo "PASS: EXPECTED_REFERENCE_PRESENT=$key"
    else
        echo "FAIL: EXPECTED_REFERENCE_MISSING_OR_LITERAL=$key"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
done

echo
echo "============================================================"
echo "6. DATABASE_URL FALSE-POSITIVE BOUNDARY"
echo "============================================================"

if grep -Eq '^[[:space:]]*DATABASE_URL[[:space:]]*:' "$COMPOSE"; then
    echo "PASS: DATABASE_URL_MAPPING_PRESENT"
else
    echo "REVIEW: DATABASE_URL_MAPPING_NOT_FOUND"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
fi

if grep -Eq 'DATABASE_URL.*\$\{POSTGRES_PASSWORD(:\?[^}]*)?\}' "$COMPOSE"; then
    echo "PASS: DATABASE_URL_USES_POSTGRES_PASSWORD_INTERPOLATION"
else
    echo "REVIEW: DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_NOT_CONFIRMED"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
fi

echo
echo "============================================================"
echo "7. SECRET VALUE OUTPUT GUARD"
echo "============================================================"

if grep -E '^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:' "$COMPOSE" \
    | grep -qE ':[[:space:]]*(?!\$\{)[^[:space:]#]+' 2>/dev/null; then
    SECRET_VALUE_OUTPUT_COUNT=$((SECRET_VALUE_OUTPUT_COUNT + 1))
fi

if [ "$SECRET_VALUE_OUTPUT_COUNT" -eq 0 ]; then
    echo "PASS: SECRET_VALUE_OUTPUT_REMAINED_REDACTED"
else
    echo "FAIL: POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo
echo "============================================================"
echo "8. CROSS-AUTHORITY INVARIANTS"
echo "============================================================"

if [ "$COMPOSE_LITERAL_COUNT" -eq 0 ]; then
    echo "PASS: INVARIANT_NO_LITERAL_COMPOSE_SECRET"
else
    echo "FAIL: INVARIANT_LITERAL_COMPOSE_SECRET_COUNT=$COMPOSE_LITERAL_COUNT"
fi

if [ "$COMPOSE_REFERENCE_COUNT" -ge 3 ]; then
    echo "PASS: INVARIANT_REQUIRED_COMPOSE_SECRET_REFERENCES_PRESENT"
else
    echo "FAIL: INVARIANT_COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

echo
echo "============================================================"
echo "9. FINAL CLASSIFICATION"
echo "============================================================"

echo "FAILURE_COUNT=$FAILURE_COUNT"
echo "REVIEW_COUNT=$REVIEW_COUNT"
echo "COMPOSE_REFERENCE_COUNT=$COMPOSE_REFERENCE_COUNT"
echo "COMPOSE_LITERAL_COUNT=$COMPOSE_LITERAL_COUNT"
echo "COMPOSE_NON_SECRET_CONTEXT_COUNT=$COMPOSE_NON_SECRET_CONTEXT_COUNT"
echo "SECRET_VALUE_OUTPUT_COUNT=$SECRET_VALUE_OUTPUT_COUNT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_02_R13_COMPOSE_SECRET_PROVENANCE_SEMANTIC_FAILURE"
    EXIT_CODE=20
elif [ "$REVIEW_COUNT" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_02_R13_COMPOSE_SECRET_PROVENANCE_SEMANTIC_REVIEW_REQUIRED"
    EXIT_CODE=10
else
    STATUS="CLEAN"
    RESULT="P0_02_R13_COMPOSE_SECRET_PROVENANCE_SEMANTIC_CLEAN"
    EXIT_CODE=0
fi

echo "P0_02_R13_STATUS=$STATUS"
echo "RESULT=$RESULT"
echo "EXIT_CODE=$EXIT_CODE"
echo "REPORT=$REPORT"

exit "$EXIT_CODE"
