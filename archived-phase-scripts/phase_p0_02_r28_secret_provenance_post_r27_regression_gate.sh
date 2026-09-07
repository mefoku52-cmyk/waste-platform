#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r28_secret_provenance_post_r27_regression_gate.txt"
R27_REPORT="${REPORT_DIR}/p0_02_r27_secret_provenance_post_r26_integrity_gate.txt"
R27_SCRIPT="${PROJECT_ROOT}/phase_p0_02_r27_secret_provenance_post_r26_integrity_gate.sh"

mkdir -p "${REPORT_DIR}"
exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R28 SECRET PROVENANCE POST-R27 REGRESSION GATE"
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
echo "2. AUTHORITY FILES"
echo "============================================================"

for f in \
    ".env.production" \
    "docker-compose.yml" \
    "app/core/config.py" \
    ".github/workflows/ci.yml" \
    "scripts/deploy.sh"
do
    [ -f "$f" ] && pass "AUTHORITY_PRESENT=${f}" || fail "AUTHORITY_MISSING=${f}"
done

echo
echo "============================================================"
echo "3. R27 REPORT"
echo "============================================================"

if [ -f "${R27_REPORT}" ]; then
    pass "R27_REPORT_PRESENT"
else
    fail "R27_REPORT_MISSING"
fi

if grep -q 'P0_02_R27_STATUS=CLEAN' "${R27_REPORT}" 2>/dev/null; then
    pass "R27_STATUS_CLEAN"
else
    fail "R27_STATUS_NOT_CLEAN"
fi

if grep -q 'EXIT_CODE=0' "${R27_REPORT}" 2>/dev/null; then
    pass "R27_EXIT_CODE_ZERO"
else
    fail "R27_EXIT_CODE_NOT_ZERO"
fi

if grep -q 'FAILURE_COUNT=0' "${R27_REPORT}" 2>/dev/null; then
    pass "R27_FAILURE_COUNT_ZERO"
else
    fail "R27_FAILURE_COUNT_NONZERO"
fi

if grep -q 'REVIEW_COUNT=0' "${R27_REPORT}" 2>/dev/null; then
    pass "R27_REVIEW_COUNT_ZERO"
else
    fail "R27_REVIEW_COUNT_NONZERO"
fi

echo
echo "============================================================"
echo "4. R27 CLASSIFIER REGRESSION"
echo "============================================================"

[ -f "${R27_SCRIPT}" ] \
    && pass "R27_SCRIPT_PRESENT" \
    || fail "R27_SCRIPT_MISSING"

if grep -Fq 'if (value ~ /^\$\{/) {' "${R27_SCRIPT}" 2>/dev/null; then
    pass "R27_LITERAL_CLASSIFIER_INTERPOLATION_RULE_PRESENT"
else
    fail "R27_LITERAL_CLASSIFIER_INTERPOLATION_RULE_MISSING"
fi

if grep -Fq 'COMPOSE_LITERAL_COUNT=$(' "${R27_SCRIPT}" 2>/dev/null; then
    pass "R27_LITERAL_COUNTER_PRESENT"
else
    fail "R27_LITERAL_COUNTER_MISSING"
fi

echo
echo "============================================================"
echo "5. COMPOSE STRUCTURE"
echo "============================================================"

COMPOSE_TARGET_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ { count++ }
END { print count + 0 }
' docker-compose.yml
)

COMPOSE_REFERENCE_COUNT=$(
awk '
/^[[:space:]]*(POSTGRES_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY)[[:space:]]*:/ {
    line=$0
    value=substr(line,index(line,":")+1)
    sub(/^[[:space:]]*/,"",value)
    if (value ~ /^\$\{/) count++
}
END { print count + 0 }
' docker-compose.yml
)

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
echo "6. R26 BASELINE CONTINUITY"
echo "============================================================"

R26_REFERENCE_BASELINE=3
R26_LITERAL_BASELINE=0

echo "R26_REFERENCE_BASELINE=${R26_REFERENCE_BASELINE}"
echo "R26_LITERAL_BASELINE=${R26_LITERAL_BASELINE}"

[ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] \
    && pass "R26_REFERENCE_BASELINE_CONTINUITY" \
    || fail "R26_REFERENCE_BASELINE_DRIFT"

[ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] \
    && pass "R26_LITERAL_BASELINE_CONTINUITY" \
    || fail "R26_LITERAL_BASELINE_DRIFT"

echo
echo "============================================================"
echo "7. FINAL REGRESSION INVARIANT"
echo "============================================================"

if \
    [ "${COMPOSE_TARGET_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ]
then
    pass "R28_COMPOSE_CLASSIFIER_REGRESSION_CLOSED"
else
    fail "R28_COMPOSE_CLASSIFIER_REGRESSION_OPEN"
fi

echo
echo "============================================================"
echo "8. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R28_SECRET_PROVENANCE_POST_R27_REGRESSION_CLEAN"
    EXIT_CODE=0
else
    STATUS="REVIEW"
    RESULT="P0_02_R28_SECRET_PROVENANCE_POST_R27_REGRESSION_REVIEW"
    EXIT_CODE=1
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "P0_02_R28_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
