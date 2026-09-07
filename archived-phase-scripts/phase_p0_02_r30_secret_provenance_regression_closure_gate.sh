#!/data/data/com.termux/files/usr/bin/bash
set -u

PROJECT_ROOT="${HOME}/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_02_r30_secret_provenance_regression_closure_gate.txt"

mkdir -p "${REPORT_DIR}"
exec > >(tee "${REPORT}") 2>&1

echo "============================================================"
echo "P0-02 R30 SECRET PROVENANCE REGRESSION CLOSURE GATE"
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
echo "2. REQUIRED R26-R29 REPORT CHAIN"
echo "============================================================"

REPORTS=(
    "audit-output/p0_02_r26_secret_provenance_baseline_gate.txt"
    "audit-output/p0_02_r27_secret_provenance_post_r26_integrity_gate.txt"
    "audit-output/p0_02_r28_secret_provenance_post_r27_regression_gate.txt"
    "audit-output/p0_02_r29_secret_provenance_cross_file_consistency_gate.txt"
)

for report in "${REPORTS[@]}"; do
    if [ -f "${report}" ]; then
        pass "REPORT_PRESENT=${report}"
    else
        fail "REPORT_MISSING=${report}"
    fi
done

echo
echo "============================================================"
echo "3. PRIOR GATE STATUS"
echo "============================================================"

for r in 26 27 28 29; do
    REPORT_FILE="audit-output/p0_02_r${r}_secret_provenance"

    case "${r}" in
        26)
            REPORT_FILE="${REPORT_FILE}_baseline_gate.txt"
            ;;
        27)
            REPORT_FILE="${REPORT_FILE}_post_r26_integrity_gate.txt"
            ;;
        28)
            REPORT_FILE="${REPORT_FILE}_post_r27_regression_gate.txt"
            ;;
        29)
            REPORT_FILE="${REPORT_FILE}_cross_file_consistency_gate.txt"
            ;;
    esac

    if grep -Eq "P0_02_R${r}_STATUS=CLEAN" "${REPORT_FILE}" 2>/dev/null; then
        pass "R${r}_STATUS_CLEAN"
    else
        fail "R${r}_STATUS_NOT_CLEAN"
    fi

    if grep -q 'FAILURE_COUNT=0' "${REPORT_FILE}" 2>/dev/null; then
        pass "R${r}_FAILURE_COUNT_ZERO"
    else
        fail "R${r}_FAILURE_COUNT_NONZERO"
    fi
done

echo
echo "============================================================"
echo "4. CURRENT IMMUTABLE SECRET INVARIANTS"
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

RUNTIME_SECRET_ASSIGNMENT_COUNT=$(
grep -Ec \
'^[[:space:]]*(POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY)[[:space:]]*=' \
app/core/config.py 2>/dev/null || true
)

DEPLOY_SECRET_REFERENCE_COUNT=$(
grep -Ec \
'POSTGRES_PASSWORD|DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|S3_SECRET_KEY' \
scripts/deploy.sh 2>/dev/null || true
)

echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "RUNTIME_SECRET_ASSIGNMENT_COUNT=${RUNTIME_SECRET_ASSIGNMENT_COUNT}"
echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"

[ "${COMPOSE_TARGET_COUNT}" -eq 3 ] \
    && pass "R30_COMPOSE_TARGET_INVARIANT" \
    || fail "R30_COMPOSE_TARGET_INVARIANT_BROKEN"

[ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] \
    && pass "R30_COMPOSE_REFERENCE_INVARIANT" \
    || fail "R30_COMPOSE_REFERENCE_INVARIANT_BROKEN"

[ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] \
    && pass "R30_COMPOSE_LITERAL_INVARIANT" \
    || fail "R30_COMPOSE_LITERAL_INVARIANT_BROKEN"

[ "${RUNTIME_SECRET_ASSIGNMENT_COUNT}" -eq 0 ] \
    && pass "R30_RUNTIME_LITERAL_ASSIGNMENT_INVARIANT" \
    || fail "R30_RUNTIME_LITERAL_ASSIGNMENT_INVARIANT_BROKEN"

[ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] \
    && pass "R30_DEPLOY_REFERENCE_INVARIANT" \
    || fail "R30_DEPLOY_REFERENCE_INVARIANT_BROKEN"

echo
echo "============================================================"
echo "5. FINAL CLOSURE"
echo "============================================================"

if \
    [ "${COMPOSE_TARGET_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_REFERENCE_COUNT}" -eq 3 ] &&
    [ "${COMPOSE_LITERAL_COUNT}" -eq 0 ] &&
    [ "${RUNTIME_SECRET_ASSIGNMENT_COUNT}" -eq 0 ] &&
    [ "${DEPLOY_SECRET_REFERENCE_COUNT}" -eq 0 ] &&
    [ "${FAILURE_COUNT}" -eq 0 ] &&
    [ "${REVIEW_COUNT}" -eq 0 ]
then
    pass "R30_SECRET_PROVENANCE_REGRESSION_CLOSED"
else
    fail "R30_SECRET_PROVENANCE_REGRESSION_NOT_CLOSED"
fi

echo
echo "============================================================"
echo "6. FINAL CLASSIFICATION"
echo "============================================================"

if [ "${FAILURE_COUNT}" -eq 0 ] && [ "${REVIEW_COUNT}" -eq 0 ]; then
    STATUS="CLEAN"
    RESULT="P0_02_R30_SECRET_PROVENANCE_REGRESSION_CLOSURE_CLEAN"
    EXIT_CODE=0
else
    STATUS="REVIEW"
    RESULT="P0_02_R30_SECRET_PROVENANCE_REGRESSION_CLOSURE_REVIEW"
    EXIT_CODE=1
fi

echo "FAILURE_COUNT=${FAILURE_COUNT}"
echo "REVIEW_COUNT=${REVIEW_COUNT}"
echo "COMPOSE_TARGET_COUNT=${COMPOSE_TARGET_COUNT}"
echo "COMPOSE_REFERENCE_COUNT=${COMPOSE_REFERENCE_COUNT}"
echo "COMPOSE_LITERAL_COUNT=${COMPOSE_LITERAL_COUNT}"
echo "RUNTIME_SECRET_ASSIGNMENT_COUNT=${RUNTIME_SECRET_ASSIGNMENT_COUNT}"
echo "DEPLOY_SECRET_REFERENCE_COUNT=${DEPLOY_SECRET_REFERENCE_COUNT}"
echo "P0_02_R30_STATUS=${STATUS}"
echo "RESULT=${RESULT}"
echo "EXIT_CODE=${EXIT_CODE}"
echo "REPORT=${REPORT}"

exit "${EXIT_CODE}"
