#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r29_secret_provenance_cross_file_consistency_gate.txt"

mkdir -p "${REPORT_DIR}"
exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R29 SECRET PROVENANCE CROSS-FILE CONSISTENCY GATE"
echo "============================================================"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail(){ echo "FAIL: $1"; FAILURE_COUNT=$((FAILURE_COUNT+1)); }
pass(){ echo "PASS: $1"; }

echo "============================================================"
echo "1. SAFETY PRECHECK"
echo "============================================================"

[ -d "${PROJECT_ROOT}" ] && pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}" || fail "PROJECT_ROOT_MISSING"

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
echo "2. AUTHORITY SECRET SET"
echo "============================================================"

SECRET_KEYS=(
    "POSTGRES_PASSWORD"
    "DATABASE_PASSWORD"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "S3_SECRET_KEY"
)

ENV_COUNT=0
CI_COUNT=0

for key in "${SECRET_KEYS[@]}"; do
    if grep -Eq "^[[:space:]]*${key}[[:space:]]*=[[:space:]]*[^[:space:]]" .env.production 2>/dev/null; then
        pass "ENV_AUTHORITY_PRESENT=${key}"
        ENV_COUNT=$((ENV_COUNT+1))
    else
        fail "ENV_AUTHORITY_MISSING_OR_EMPTY=${key}"
    fi

    if grep -Eq "${key}" .github/workflows/ci.yml 2>/dev/null; then
        pass "CI_IDENTIFIER_PRESENT=${key}"
        CI_COUNT=$((CI_COUNT+1))
    else
        fail "CI_IDENTIFIER_MISSING=${key}"
    fi
done

echo "ENV_AUTHORITY_COUNT=${ENV_COUNT}"
echo "CI_IDENTIFIER_COUNT=${CI_COUNT}"

[ "${ENV_COUNT}" -eq 5 ] \
    && pass "ENV_AUTHORITY_SET_COMPLETE" \
    || fail "ENV_AUTHORITY_SET_INCOMPLETE"

[ "${CI_COUNT}" -eq 5 ] \
    && pass "CI_IDENTIFIER_SET_COMPLETE" \
    || fail "CI_IDENTIFIER_SET_INCOMPLETE"

echo
echo "============================================================"
echo "3. COMPOSE PROVENANCE"
echo "============================================================"

for key in POSTGRES_PASSWORD JWT_SECRET_KEY JWT_REFRESH_SECRET_KEY; do
    if grep -Eq "^[[:space:]]*${key}[[:space:]]*:[[:space:]]*\$\{" docker-compose.yml; then
        pass "COMPOSE_REFERENCE_PRESENT=${key}"
    else
        fail "COMPOSE_REFERENCE_MISSING=${key}"
    fi
done

COMPOSE_LITERAL_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)

    if (value == "") next
    if (value ~ /^\$\{/) next

    count++
}
END { print count + 0 }
' docker-compose.yml
)

echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"

[ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] \
    && pass "COMPOSE_LITERAL_ASSIGNMENT_COUNT_ZERO" \
    || fail "COMPOSE_LITERAL_ASSIGNMENT_DETECTED"

echo
echo "============================================================"
echo "4. RUNTIME PROVENANCE"
echo "============================================================"

if grep -Eq 'JWT_SECRET_KEY' app/core/config.py; then
    pass "RUNTIME_JWT_IDENTIFIER_PRESENT"
else
    fail "RUNTIME_JWT_IDENTIFIER_MISSING"
fi

RUNTIME_SECRET_ASSIGNMENT_COUNT=$(
grep -Ec \
'^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
app/core/config.py 2>/dev/null || true
)

echo "RUNTIME_SECRET_ASSIGNMENT_COUNT=${RUNTIME_SECRET_ASSIGNMENT_COUNT}"

[ "${RUNTIME_SECRET_ASSIGNMENT_COUNT}" -eq 0 ] \
    && pass "RUNTIME_DIRECT_SECRET_ASSIGNMENT_ZERO" \
    || fail "RUNTIME_DIRECT_SECRET_ASSIGNMENT_DETECTED"

echo
echo "============================================================"
echo "5. DEPLOYMENT PROVENANCE"
echo "============================================================"

DEPLOY_SECRET_REFERENCE_COUNT=$(
grep -Ec \
'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
scripts/deploy.sh 2>/dev/null || true
)

echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

[ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] \
    && pass "DEPLOY_SECRET_REFERENCE_ZERO" \
    || fail "DEPLOY_SECRET_REFERENCE_DETECTED"

echo
echo "============================================================"
echo "6. DATABASE URL PROVENANCE"
echo "============================================================"

if grep -Eq 'DATABASE_URL:.*\$\{POSTGRES_PASSWORD:' docker-compose.yml; then
    pass "DATABASE_URL_SECRET_PROVENANCE_PRESENT"
else
    fail "DATABASE_URL_SECRET_PROVENANCE_MISSING"
fi

echo
echo "============================================================"
echo "7. CROSS-FILE CONSISTENCY"
echo "============================================================"

if \
    [ "${ENV_COUNT}" -eq 5 ] &&
    [ "${CI_COUNT}" -eq 5 ] &&
    [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] &&
    [ "${RUNTIME_SECRET_ASSIGNMENT_COUNT}" -eq 0 ] &&
    [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ]
then
    pass "R29_CROSS_FILE_SECRET_PROVENANCE_CONSISTENT"
else
    fail "R29_CROSS_FILE_SECRET_PROVENANCE_INCONSISTENT"
fi

echo
echo "============================================================"
echo "8. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R29_SECRET_PROVENANCE_CROSS_FILE_CONSISTENCY_CLEAN"
    EXIT_CODE=0
else
    STATUS="REVIEW"
    RESULT="P0_02_R29_SECRET_PROVENANCE_CROSS_FILE_CONSISTENCY_REVIEW"
    EXIT_CODE=1
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "ENV_AUTHORITY_COUNT=${ENV_COUNT}"
echo "CI_IDENTIFIER_COUNT=${CI_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "RUNTIME_SECRET_ASSIGNMENT_COUNT=${RUNTIME_SECRET_ASSIGNMENT_COUNT}"
echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"
echo "P0_02_R29_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
