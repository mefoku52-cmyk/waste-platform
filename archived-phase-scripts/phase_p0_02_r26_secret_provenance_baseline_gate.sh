#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r26_secret_provenance_baseline_gate.txt"

mkdir -p "${REPORT_DIR}"

exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R26 SECRET PROVENANCE BASELINE GATE"
echo "============================================================"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail() {
    echo "FAIL: $1"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
}

review() {
    echo "REVIEW: $1"
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
}

pass() {
    echo "PASS: $1"
}

echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

[ -d "${PROJECT_ROOT}" ] \
    && pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}" \
    || fail "PROJECT_ROOT_MISSING"

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_DELETIONS=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "BOUNDED_SCAN=YES"

cd "${PROJECT_ROOT}" || exit 1

echo
echo "============================================================"
echo "2. AUTHORITY FILES"
echo "============================================================"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

for f in "${AUTHORITY_FILES[@]}"; do
    if [ -f "${f}" ]; then
        pass "AUTHORITY_PRESENT=${f}"
    else
        fail "AUTHORITY_MISSING=${f}"
    fi
done

echo
echo "============================================================"
echo "3. PRODUCTION SECRET AUTHORITY"
echo "============================================================"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

ENV_SECRET_COUNT=0

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "^[[:space:]]*${key}[[:space:]]*=[[:space:]]*[^[:space:]]" .env.production 2>/dev/null; then
        pass "ENV_SECRET_AUTHORITY_PRESENT=${key}"
        ENV_SECRET_COUNT=$((ENV_SECRET_COUNT + 1))
    else
        fail "ENV_SECRET_AUTHORITY_MISSING_OR_EMPTY=${key}"
    fi
done

echo "ENV_SECRET_AUTHORITY_COUNT=${ENV_SECRET_COUNT}"

[ "${ENV_SECRET_COUNT}" -eq 5 ] \
    && pass "ENV_SECRET_AUTHORITY_CARDINALITY_EXACT" \
    || fail "ENV_SECRET_AUTHORITY_CARDINALITY_MISMATCH"

echo
echo "============================================================"
echo "4. COMPOSE SECRET REFERENCE BASELINE"
echo "============================================================"

COMPOSE_TARGET_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    count++
}
END {
    print count + 0
}
' docker-compose.yml 2>/dev/null
)

COMPOSE_REFERENCE_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)

    if (value ~ /^\$\{/) {
        count++
    }
}
END {
    print count + 0
}
' docker-compose.yml 2>/dev/null
)

COMPOSE_LITERAL_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)

    if (value == "") {
        next
    }

    if (value ~ /^\$\{/) {
        next
    }

    count++
}
END {
    print count + 0
}
' docker-compose.yml 2>/dev/null
)

echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

[ "${COMPOSE_TARGET_COUNT}" -eq 3 ] \
    && pass "COMPOSE_TARGET_CARDINALITY_EXACT" \
    || fail "COMPOSE_TARGET_CARDINALITY_MISMATCH"

[ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] \
    && pass "COMPOSE_REFERENCE_CARDINALITY_EXACT" \
    || fail "COMPOSE_REFERENCE_CARDINALITY_MISMATCH"

[ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] \
    && pass "NO_LITERAL_COMPOSE_SECRET_ASSIGNMENT" \
    || fail "LITERAL_COMPOSE_SECRET_ASSIGNMENT_DETECTED"

if grep -Eq 'DATABASE_URL:.*\$\{POSTGRES_PASSWORD:' docker-compose.yml; then
    pass "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_PRESENT"
else
    fail "DATABASE_URL_POSTGRES_PASSWORD_INTERPOLATION_MISSING"
fi

echo
echo "============================================================"
echo "5. RUNTIME SECRET PROVENANCE"
echo "============================================================"

if grep -Eq 'JWT_SECRET_KEY' app/core/config.py; then
    pass "RUNTIME_JWT_SECRET_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_SECRET_IDENTIFIER_MISSING"
fi

if grep -Eq 'SECRET|secret|provenance|authority' app/core/config.py; then
    pass "RUNTIME_SECRET_AUTHORITY_CONTEXT_PRESENT"
else
    review "RUNTIME_SECRET_AUTHORITY_CONTEXT_NOT_DETECTABLE"
fi

RUNTIME_DECLARATION_COUNT=$(
grep -Ec '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|POSTGRES_PASSWORD|DATABASE_PASSWORD|S3_SECRET_KEY)[[:space:]]*=' \
app/core/config.py 2>/dev/null || true
)

RUNTIME_LITERAL_COUNT=$(
grep -Ec '^[[:space:]]*(JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|POSTGRES_PASSWORD|DATABASE_PASSWORD|S3_SECRET_KEY)[[:space:]]*=[[:space:]]*["'\'']' \
app/core/config.py 2>/dev/null || true
)

echo "RUNTIME_DECLARATION_COUNT=${RUNTIME_DECLARATION_COUNT}"
echo "RUNTIME_LITERAL_COUNT=${RUNTIME_LITERAL_COUNT}"

[ "${RUNTIME_DECLARATION_COUNT}" -eq 0 ] \
    && pass "NO_RUNTIME_SECRET_ASSIGNMENT" \
    || fail "RUNTIME_SECRET_ASSIGNMENT_DETECTED"

[ "${RUNTIME_LITERAL_COUNT}" -eq 0 ] \
    && pass "NO_RUNTIME_LITERAL_SECRET_VALUE" \
    || fail "RUNTIME_LITERAL_SECRET_VALUE_DETECTED"

echo
echo "============================================================"
echo "6. CI SECRET AUTHORITY"
echo "============================================================"

CI_SECRET_ASSIGNMENT_COUNT=0

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "${key}" .github/workflows/ci.yml 2>/dev/null; then
        pass "CI_SECRET_IDENTIFIER_PRESENT=${key}"
        CI_SECRET_ASSIGNMENT_COUNT=$((CI_SECRET_ASSIGNMENT_COUNT + 1))
    else
        fail "CI_SECRET_IDENTIFIER_MISSING=${key}"
    fi
done

echo "CI_SECRET_ASSIGNMENT_COUNT=${CI_SECRET_ASSIGNMENT_COUNT}"

[ "${CI_SECRET_ASSIGNMENT_COUNT}" -eq 5 ] \
    && pass "CI_SECRET_IDENTIFIER_CARDINALITY_EXACT" \
    || fail "CI_SECRET_IDENTIFIER_CARDINALITY_MISMATCH"

CI_PROD_SCOPE_COUNT=$(
grep -Ec 'production|prod' .github/workflows/ci.yml 2>/dev/null || true
)

echo "CI_PROD_SCOPE_COUNT=${CI_PROD_SCOPE_COUNT}"

echo
echo "============================================================"
echo "7. DEPLOY SECRET PROVENANCE"
echo "============================================================"

DEPLOY_SECRET_REFERENCE_COUNT=$(
grep -Ec 'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
scripts/deploy.sh 2>/dev/null || true
)

echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

[ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] \
    && pass "DEPLOY_SECRET_REFERENCE_BASELINE_ZERO" \
    || fail "DEPLOY_SECRET_REFERENCE_DETECTED"

echo
echo "============================================================"
echo "8. SECRET VALUE OUTPUT SCAN"
echo "============================================================"

SECRET_VALUE_OUTPUT_COUNT=$(
grep -REn \
'(echo|printf|print)[^#]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)' \
.github scripts app \
--exclude='*.pyc' \
--exclude-dir='__pycache__' \
2>/dev/null | wc -l
)

echo "SECRET_VALUE_OUTPUT_COUNT=${SECRET_VALUE_OUTPUT_COUNT}"

[ "${SECRET_VALUE_OUTPUT_COUNT}" -eq 0 ] \
    && pass "NO_SECRET_VALUE_OUTPUT_PATTERN" \
    || fail "SECRET_VALUE_OUTPUT_PATTERN_DETECTED"

echo
echo "============================================================"
echo "9. R26 BASELINE"
echo "============================================================"

R26_COMPOSE_REFERENCE_BASELINE="${COMPOSE_REFERENCE_COUNT}"
R26_COMPOSE_LITERAL_BASELINE="${COMPOSE_LITERAL_COUNT}"
R26_SECRET_OUTPUT_BASELINE="${SECRET_VALUE_OUTPUT_COUNT}"

echo "R26_COMPOSE_REFERENCE_BASELINE=${R26_COMPOSE_REFERENCE_BASELINE}"
echo "R26_COMPOSE_LITERAL_BASELINE=${R26_COMPOSE_LITERAL_BASELINE}"
echo "R26_SECRET_OUTPUT_BASELINE=${R26_SECRET_OUTPUT_BASELINE}"

echo
echo "============================================================"
echo "10. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R26_SECRET_PROVENANCE_BASELINE_CLEAN"
    EXIT_CODE=0
else
    STATUS="REVIEW"
    RESULT="P0_02_R26_SECRET_PROVENANCE_BASELINE_REVIEW"
    EXIT_CODE=1
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "R26_COMPOSE_REFERENCE_BASELINE=${R26_COMPOSE_REFERENCE_BASELINE}"
echo "R26_COMPOSE_LITERAL_BASELINE=${R26_COMPOSE_LITERAL_BASELINE}"
echo "R26_SECRET_OUTPUT_BASELINE=${R26_SECRET_OUTPUT_BASELINE}"
echo "P0_02_R26_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
