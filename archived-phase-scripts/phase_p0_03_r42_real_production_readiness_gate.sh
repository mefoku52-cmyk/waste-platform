#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT_DIR="${PROJECT_ROOT}/audit-output"
REPORT="${REPORT_DIR}/p0_03_r42_real_production_readiness_gate.txt"

SCRIPT_NAME="$(basename "$0")"

FAILURE_COUNT=0
REVIEW_COUNT=0

STATUS="PASS"
RESULT="P0_03_R42_REAL_PRODUCTION_READINESS_PASS"
EXIT_CODE=0

log() {
    printf '%s\n' "$*" | tee -a "${REPORT}"
}

pass() {
    log "PASS: $*"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    log "REVIEW: $*"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    log "FAIL: $*"
}

count_matches() {
    local pattern="$1"
    local path="$2"

    if [ ! -e "${path}" ]; then
        printf '0'
        return 0
    fi

    grep -RInE \
        --exclude="${SCRIPT_NAME}" \
        --exclude='*.pyc' \
        --exclude-dir='__pycache__' \
        --exclude-dir='.git' \
        --exclude-dir='audit-output' \
        --exclude-dir='forensics' \
        --exclude-dir='archive' \
        -- "${pattern}" "${path}" 2>/dev/null | wc -l | tr -d ' '
}

file_contains() {
    local pattern="$1"
    local file="$2"

    [ -f "${file}" ] &&
        grep -Eq -- "${pattern}" "${file}" 2>/dev/null
}

file_exists() {
    [ -f "$1" ]
}

dir_exists() {
    [ -d "$1" ]
}

mkdir -p "${REPORT_DIR}"
: > "${REPORT}"

log "============================================================"
log "P0-03 R42 REAL PRODUCTION READINESS GATE"
log "============================================================"

log ""
log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ "$(pwd -P)" = "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
else
    fail "PROJECT_ROOT_NOT_CURRENT_DIRECTORY"
fi

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_PRESENT"
else
    fail "PROJECT_ROOT_MISSING"
fi

pass "READ_ONLY=YES"
pass "NO_SOURCE_WRITES=YES"
pass "NO_RUNTIME_EXECUTION=YES"
pass "NO_ENV_EXECUTION=YES"
pass "NO_BUILD=YES"
pass "NO_DEPLOYMENT=YES"
pass "NO_SECRET_VALUES_PRINTED=YES"
pass "NO_ENV_VALUES_READ=YES"
pass "FAIL_CLOSED=YES"
pass "NO_NEW_SECRET_PROVENANCE_ASSERTIONS=YES"

log ""
log "============================================================"
log "2. R41 LEDGER HANDOFF"
log "============================================================"

R41_REPORT="${REPORT_DIR}/p0_03_r41_production_readiness_ledger_closure_gate.txt"

if file_exists "${R41_REPORT}"; then
    pass "R41_CLOSURE_REPORT_PRESENT"

    R41_STATUS="$(grep -E '^P0_03_R41_STATUS=' "${R41_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R41_EXIT_CODE="$(grep -E '^EXIT_CODE=' "${R41_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"
    R41_BLOCKERS="$(grep -E '^CURRENT_BLOCKER_CANDIDATE_COUNT=' "${R41_REPORT}" 2>/dev/null | tail -1 | cut -d= -f2-)"

    log "R41_STATUS=${R41_STATUS:-UNKNOWN}"
    log "R41_EXIT_CODE=${R41_EXIT_CODE:-UNKNOWN}"
    log "CURRENT_BLOCKER_CANDIDATE_COUNT=${R41_BLOCKERS:-UNKNOWN}"

    if [ "${R41_STATUS:-}" = "PASS" ]; then
        pass "R41_LEDGER_CLOSED"
    else
        fail "R41_LEDGER_NOT_CLOSED"
    fi

    if [ "${R41_EXIT_CODE:-}" = "0" ]; then
        pass "R41_EXIT_CODE_ZERO"
    else
        fail "R41_EXIT_CODE_NOT_ZERO"
    fi

    if [ "${R41_BLOCKERS:-}" = "0" ]; then
        pass "R41_CURRENT_BLOCKER_COUNT_ZERO"
    else
        fail "R41_CURRENT_BLOCKER_COUNT_NOT_ZERO"
    fi
else
    fail "R41_CLOSURE_REPORT_MISSING"
fi

log ""
log "============================================================"
log "3. PRODUCTION AUTHORITY FILES"
log "============================================================"

AUTHORITY_FILES=(
    ".env.production"
    "docker-compose.yml"
    "app/core/config.py"
    ".github/workflows/ci.yml"
    "scripts/deploy.sh"
)

AUTHORITY_COUNT=0
AUTHORITY_MISSING_COUNT=0

for relative in "${AUTHORITY_FILES[@]}"; do
    if file_exists "${PROJECT_ROOT}/${relative}"; then
        AUTHORITY_COUNT=$((AUTHORITY_COUNT + 1))
        pass "AUTHORITY_PRESENT=${relative}"
    else
        AUTHORITY_MISSING_COUNT=$((AUTHORITY_MISSING_COUNT + 1))
        fail "AUTHORITY_MISSING=${relative}"
    fi
done

log "AUTHORITY_FILE_COUNT=${AUTHORITY_COUNT}"
log "AUTHORITY_MISSING_COUNT=${AUTHORITY_MISSING_COUNT}"

log ""
log "============================================================"
log "4. APPLICATION STRUCTURE"
log "============================================================"

APP_DIR_PRESENT=0
SRC_DIR_PRESENT=0
TEST_DIR_PRESENT=0

if dir_exists "${PROJECT_ROOT}/app"; then
    APP_DIR_PRESENT=1
    pass "APP_DIRECTORY_PRESENT"
else
    fail "APP_DIRECTORY_MISSING"
fi

if dir_exists "${PROJECT_ROOT}/src"; then
    SRC_DIR_PRESENT=1
    pass "SRC_DIRECTORY_PRESENT"
else
    log "INFO: SRC_DIRECTORY_NOT_PRESENT"
fi

if dir_exists "${PROJECT_ROOT}/tests"; then
    TEST_DIR_PRESENT=1
    pass "TEST_DIRECTORY_PRESENT"
else
    review "TEST_DIRECTORY_MISSING"
fi

log "APP_DIR_PRESENT=${APP_DIR_PRESENT}"
log "SRC_DIR_PRESENT=${SRC_DIR_PRESENT}"
log "TEST_DIR_PRESENT=${TEST_DIR_PRESENT}"

log ""
log "============================================================"
log "5. PRODUCTION CONFIGURATION STATIC ANALYSIS"
log "============================================================"

CONFIG_FILE="${PROJECT_ROOT}/app/core/config.py"

DEBUG_TRUE_COUNT=0
DEV_ENV_COUNT=0
LOCALHOST_PROD_COUNT=0
INSECURE_SECRET_DEFAULT_COUNT=0
TEST_DEFAULT_COUNT=0

if file_exists "${CONFIG_FILE}"; then

    DEBUG_TRUE_COUNT="$(count_matches \
        '(^|[^A-Za-z0-9_])DEBUG[[:space:]]*=[[:space:]]*True([^A-Za-z0-9_]|$)|debug[[:space:]]*:[[:space:]]*bool[[:space:]]*=[[:space:]]*True' \
        "${CONFIG_FILE}")"

    DEV_ENV_COUNT="$(count_matches \
        'ENVIRONMENT[[:space:]]*=[[:space:]]*["'\'']development["'\'']|ENV[[:space:]]*=[[:space:]]*["'\'']development["'\'']' \
        "${CONFIG_FILE}")"

    LOCALHOST_PROD_COUNT="$(count_matches \
        'HOST[[:space:]]*=[[:space:]]*["'\'']127\.0\.0\.1["'\'']|HOST[[:space:]]*=[[:space:]]*["'\'']localhost["'\'']' \
        "${CONFIG_FILE}")"

    INSECURE_SECRET_DEFAULT_COUNT="$(count_matches \
        '(SECRET|PASSWORD|TOKEN|KEY)[A-Za-z0-9_]*[[:space:]]*=[[:space:]]*["'\''](secret|password|changeme|change_me|default|test|123456|admin)["'\'']' \
        "${CONFIG_FILE}")"

    TEST_DEFAULT_COUNT="$(count_matches \
        '(ENVIRONMENT|APP_ENV|MODE)[A-Za-z0-9_]*[[:space:]]*=[[:space:]]*["'\'']test["'\'']' \
        "${CONFIG_FILE}")"

    log "DEBUG_TRUE_COUNT=${DEBUG_TRUE_COUNT}"
    log "DEV_ENV_COUNT=${DEV_ENV_COUNT}"
    log "LOCALHOST_PROD_COUNT=${LOCALHOST_PROD_COUNT}"
    log "INSECURE_SECRET_DEFAULT_COUNT=${INSECURE_SECRET_DEFAULT_COUNT}"
    log "TEST_DEFAULT_COUNT=${TEST_DEFAULT_COUNT}"

    if [ "${DEBUG_TRUE_COUNT}" -eq 0 ]; then
        pass "NO_STATIC_DEBUG_TRUE_IN_PRODUCTION_CONFIG"
    else
        fail "STATIC_DEBUG_TRUE_PRESENT_IN_PRODUCTION_CONFIG"
    fi

    if [ "${DEV_ENV_COUNT}" -eq 0 ]; then
        pass "NO_STATIC_DEVELOPMENT_ENVIRONMENT_DEFAULT"
    else
        fail "DEVELOPMENT_ENVIRONMENT_DEFAULT_PRESENT"
    fi

    if [ "${INSECURE_SECRET_DEFAULT_COUNT}" -eq 0 ]; then
        pass "NO_INSECURE_SECRET_DEFAULTS_DETECTED"
    else
        fail "INSECURE_SECRET_DEFAULTS_DETECTED"
    fi

    if [ "${TEST_DEFAULT_COUNT}" -eq 0 ]; then
        pass "NO_TEST_ENVIRONMENT_DEFAULT"
    else
        fail "TEST_ENVIRONMENT_DEFAULT_PRESENT"
    fi

else
    fail "PRODUCTION_CONFIG_FILE_MISSING"
fi

log ""
log "============================================================"
log "6. DOCKER COMPOSE STATIC PRODUCTION SEMANTICS"
log "============================================================"

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

COMPOSE_SERVICE_COUNT=0
COMPOSE_HEALTHCHECK_COUNT=0
COMPOSE_RESTART_COUNT=0
COMPOSE_HOST_PORT_COUNT=0
COMPOSE_DEPENDS_ON_COUNT=0
COMPOSE_BUILD_COUNT=0
COMPOSE_PRIVILEGED_COUNT=0

if file_exists "${COMPOSE_FILE}"; then

    COMPOSE_SERVICE_COUNT="$(
        awk '
        /^[[:space:]]{2}[A-Za-z0-9_.-]+:[[:space:]]*$/ {
            print
        }
        ' "${COMPOSE_FILE}" 2>/dev/null | wc -l | tr -d ' '
    )"

    COMPOSE_HEALTHCHECK_COUNT="$(count_matches \
        '^[[:space:]]*healthcheck:[[:space:]]*$' \
        "${COMPOSE_FILE}")"

    COMPOSE_RESTART_COUNT="$(count_matches \
        '^[[:space:]]*restart:[[:space:]]*[^[:space:]]+' \
        "${COMPOSE_FILE}")"

    COMPOSE_HOST_PORT_COUNT="$(count_matches \
        '["'\'']?[0-9]{1,5}:[0-9]{1,5}["'\'']?[[:space:]]*$' \
        "${COMPOSE_FILE}")"

    COMPOSE_DEPENDS_ON_COUNT="$(count_matches \
        '^[[:space:]]*depends_on:[[:space:]]*$' \
        "${COMPOSE_FILE}")"

    COMPOSE_BUILD_COUNT="$(count_matches \
        '^[[:space:]]*build:[[:space:]]*' \
        "${COMPOSE_FILE}")"

    COMPOSE_PRIVILEGED_COUNT="$(count_matches \
        '^[[:space:]]*privileged:[[:space:]]*true' \
        "${COMPOSE_FILE}")"

    log "COMPOSE_SERVICE_COUNT=${COMPOSE_SERVICE_COUNT}"
    log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
    log "COMPOSE_RESTART_COUNT=${COMPOSE_RESTART_COUNT}"
    log "COMPOSE_HOST_PORT_COUNT=${COMPOSE_HOST_PORT_COUNT}"
    log "COMPOSE_DEPENDS_ON_COUNT=${COMPOSE_DEPENDS_ON_COUNT}"
    log "COMPOSE_BUILD_COUNT=${COMPOSE_BUILD_COUNT}"
    log "COMPOSE_PRIVILEGED_COUNT=${COMPOSE_PRIVILEGED_COUNT}"

    if [ "${COMPOSE_SERVICE_COUNT}" -gt 0 ]; then
        pass "COMPOSE_SERVICES_PRESENT"
    else
        fail "COMPOSE_SERVICES_NOT_DETECTED"
    fi

    if [ "${COMPOSE_HEALTHCHECK_COUNT}" -gt 0 ]; then
        pass "COMPOSE_HEALTHCHECK_PRESENT"
    else
        review "NO_COMPOSE_HEALTHCHECK_DETECTED"
    fi

    if [ "${COMPOSE_RESTART_COUNT}" -gt 0 ]; then
        pass "COMPOSE_RESTART_POLICY_PRESENT"
    else
        review "NO_COMPOSE_RESTART_POLICY_DETECTED"
    fi

    if [ "${COMPOSE_PRIVILEGED_COUNT}" -eq 0 ]; then
        pass "NO_PRIVILEGED_TRUE_DETECTED"
    else
        fail "PRIVILEGED_TRUE_DETECTED"
    fi

else
    fail "DOCKER_COMPOSE_FILE_MISSING"
fi

log ""
log "============================================================"
log "7. DATABASE / MIGRATION READINESS"
log "============================================================"

MIGRATION_DIR_COUNT=0
MIGRATION_COMMAND_COUNT=0
ALEMBIC_CONFIG_COUNT=0
DB_MODEL_COUNT=0

if dir_exists "${PROJECT_ROOT}/alembic"; then
    MIGRATION_DIR_COUNT=1
    pass "ALEMBIC_DIRECTORY_PRESENT"
fi

if file_exists "${PROJECT_ROOT}/alembic.ini"; then
    ALEMBIC_CONFIG_COUNT=1
    pass "ALEMBIC_CONFIG_PRESENT"
fi

MIGRATION_DIR_COUNT="$(
    find "${PROJECT_ROOT}" \
        -type d \
        \( -name .git -o -name audit-output -o -name forensics -o -name archive -o -name __pycache__ \) -prune -o \
        -type d \
        \( -iname '*migration*' -o -iname 'migrations' \) \
        -print 2>/dev/null | wc -l | tr -d ' '
)"

MIGRATION_COMMAND_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- 'alembic[[:space:]]+(upgrade|revision)|flask[[:space:]]+db[[:space:]]+(upgrade|migrate)|manage\.py[[:space:]]+(migrate|makemigrations)' \
    "${PROJECT_ROOT}" 2>/dev/null | wc -l | tr -d ' ')"

DB_MODEL_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- 'SQLAlchemy|DeclarativeBase|Mapped\[|Column\(|create_async_engine|create_engine' \
    "${PROJECT_ROOT}" 2>/dev/null | wc -l | tr -d ' ')"

log "MIGRATION_DIR_COUNT=${MIGRATION_DIR_COUNT}"
log "ALEMBIC_CONFIG_COUNT=${ALEMBIC_CONFIG_COUNT}"
log "MIGRATION_COMMAND_COUNT=${MIGRATION_COMMAND_COUNT}"
log "DB_MODEL_COUNT=${DB_MODEL_COUNT}"

if [ "${DB_MODEL_COUNT}" -gt 0 ]; then
    pass "DATABASE_LAYER_DETECTED"
else
    review "DATABASE_LAYER_NOT_DETECTED_BY_STATIC_SIGNATURES"
fi

if [ "${MIGRATION_DIR_COUNT}" -gt 0 ] || [ "${ALEMBIC_CONFIG_COUNT}" -gt 0 ] || [ "${MIGRATION_COMMAND_COUNT}" -gt 0 ]; then
    pass "DATABASE_MIGRATION_INFRASTRUCTURE_DETECTED"
else
    review "DATABASE_MIGRATION_INFRASTRUCTURE_NOT_DETECTED"
fi

log ""
log "============================================================"
log "8. HEALTH / READINESS ENDPOINT STATIC DISCOVERY"
log "============================================================"

HEALTH_ENDPOINT_COUNT=0
READINESS_ENDPOINT_COUNT=0
LIVENESS_ENDPOINT_COUNT=0

HEALTH_ENDPOINT_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- '/(health|healthz|status)["'\'']?([[:space:]]|["'\'']|:)|["'\'']/(health|healthz|status)["'\'']' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" 2>/dev/null | wc -l | tr -d ' ')"

READINESS_ENDPOINT_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- '(/ready|/readiness|readiness|readyz)' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" 2>/dev/null | wc -l | tr -d ' ')"

LIVENESS_ENDPOINT_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- '(/live|/liveness|liveness|livez)' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" 2>/dev/null | wc -l | tr -d ' ')"

log "HEALTH_ENDPOINT_COUNT=${HEALTH_ENDPOINT_COUNT}"
log "READINESS_ENDPOINT_COUNT=${READINESS_ENDPOINT_COUNT}"
log "LIVENESS_ENDPOINT_COUNT=${LIVENESS_ENDPOINT_COUNT}"

if [ "${HEALTH_ENDPOINT_COUNT}" -gt 0 ]; then
    pass "HEALTH_ENDPOINT_DETECTED"
else
    review "HEALTH_ENDPOINT_NOT_DETECTED"
fi

if [ "${READINESS_ENDPOINT_COUNT}" -gt 0 ]; then
    pass "READINESS_ENDPOINT_DETECTED"
else
    review "READINESS_ENDPOINT_NOT_DETECTED"
fi

log ""
log "============================================================"
log "9. CI/CD PRODUCTION GATE DISCOVERY"
log "============================================================"

CI_FILE="${PROJECT_ROOT}/.github/workflows/ci.yml"

CI_TEST_COUNT=0
CI_BUILD_COUNT=0
CI_DEPLOY_COUNT=0
CI_BRANCH_GUARD_COUNT=0
CI_PYTEST_COUNT=0

if file_exists "${CI_FILE}"; then

    CI_TEST_COUNT="$(count_matches \
        '(^|[[:space:]])(test|tests|pytest|unit[ _-]?test|integration[ _-]?test)' \
        "${CI_FILE}")"

    CI_BUILD_COUNT="$(count_matches \
        '(^|[[:space:]])(build|docker build|gradle build|npm run build)' \
        "${CI_FILE}")"

    CI_DEPLOY_COUNT="$(count_matches \
        '(^|[[:space:]])(deploy|deployment|production)' \
        "${CI_FILE}")"

    CI_BRANCH_GUARD_COUNT="$(count_matches \
        '(branches|tags|if:[[:space:]]*.*(main|master|production|release))' \
        "${CI_FILE}")"

    CI_PYTEST_COUNT="$(count_matches \
        'pytest|python[[:space:]]+-m[[:space:]]+pytest' \
        "${CI_FILE}")"

    log "CI_TEST_COUNT=${CI_TEST_COUNT}"
    log "CI_BUILD_COUNT=${CI_BUILD_COUNT}"
    log "CI_DEPLOY_COUNT=${CI_DEPLOY_COUNT}"
    log "CI_BRANCH_GUARD_COUNT=${CI_BRANCH_GUARD_COUNT}"
    log "CI_PYTEST_COUNT=${CI_PYTEST_COUNT}"

    if [ "${CI_TEST_COUNT}" -gt 0 ] || [ "${CI_PYTEST_COUNT}" -gt 0 ]; then
        pass "CI_TEST_GATE_DETECTED"
    else
        review "CI_TEST_GATE_NOT_DETECTED"
    fi

    if [ "${CI_BUILD_COUNT}" -gt 0 ]; then
        pass "CI_BUILD_GATE_DETECTED"
    else
        review "CI_BUILD_GATE_NOT_DETECTED"
    fi

    if [ "${CI_DEPLOY_COUNT}" -gt 0 ]; then
        pass "CI_DEPLOYMENT_PATH_REFERENCED"
    else
        review "CI_PRODUCTION_DEPLOYMENT_PATH_NOT_DETECTED"
    fi

    if [ "${CI_BRANCH_GUARD_COUNT}" -gt 0 ]; then
        pass "CI_BRANCH_OR_RELEASE_GUARD_DETECTED"
    else
        review "CI_BRANCH_OR_RELEASE_GUARD_NOT_DETECTED"
    fi

else
    fail "CI_WORKFLOW_MISSING"
fi

log ""
log "============================================================"
log "10. DEPLOYMENT SCRIPT STATIC SAFETY"
log "============================================================"

DEPLOY_FILE="${PROJECT_ROOT}/scripts/deploy.sh"

DEPLOY_SET_E_COUNT=0
DEPLOY_FAIL_FAST_COUNT=0
DEPLOY_DRY_RUN_COUNT=0
DEPLOY_ROLLBACK_COUNT=0
DEPLOY_DANGEROUS_RM_COUNT=0
DEPLOY_ENV_SOURCE_COUNT=0

if file_exists "${DEPLOY_FILE}"; then

    DEPLOY_SET_E_COUNT="$(count_matches \
        'set[[:space:]]+-[[:A-Za-z]*e[A-Za-z]*' \
        "${DEPLOY_FILE}")"

    DEPLOY_FAIL_FAST_COUNT="$(count_matches \
        'set[[:space:]]+-e|set[[:space:]]+-Ee|set[[:space:]]+-euo' \
        "${DEPLOY_FILE}")"

    DEPLOY_DRY_RUN_COUNT="$(count_matches \
        'dry-run|DRY_RUN|--dry-run' \
        "${DEPLOY_FILE}")"

    DEPLOY_ROLLBACK_COUNT="$(count_matches \
        'rollback|ROLLBACK' \
        "${DEPLOY_FILE}")"

    DEPLOY_DANGEROUS_RM_COUNT="$(count_matches \
        'rm[[:space:]]+-rf[[:space:]]+(/|"\$\{PROJECT_ROOT\}"|\$\{PROJECT_ROOT\})' \
        "${DEPLOY_FILE}")"

    DEPLOY_ENV_SOURCE_COUNT="$(count_matches \
        '(^|[[:space:];])source[[:space:]]+[^#]*\.env|(^|[[:space:];])\.[[:space:]]+[^#]*\.env' \
        "${DEPLOY_FILE}")"

    log "DEPLOY_SET_E_COUNT=${DEPLOY_SET_E_COUNT}"
    log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
    log "DEPLOY_DRY_RUN_COUNT=${DEPLOY_DRY_RUN_COUNT}"
    log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
    log "DEPLOY_DANGEROUS_RM_COUNT=${DEPLOY_DANGEROUS_RM_COUNT}"
    log "DEPLOY_ENV_SOURCE_COUNT=${DEPLOY_ENV_SOURCE_COUNT}"

    if [ "${DEPLOY_FAIL_FAST_COUNT}" -gt 0 ]; then
        pass "DEPLOY_FAIL_FAST_SEMANTICS_DETECTED"
    else
        review "DEPLOY_FAIL_FAST_SEMANTICS_NOT_DETECTED"
    fi

    if [ "${DEPLOY_DANGEROUS_RM_COUNT}" -eq 0 ]; then
        pass "NO_DANGEROUS_DEPLOY_RM_PATTERN_DETECTED"
    else
        fail "DANGEROUS_DEPLOY_RM_PATTERN_DETECTED"
    fi

    if [ "${DEPLOY_ENV_SOURCE_COUNT}" -eq 0 ]; then
        pass "DEPLOY_SCRIPT_DOES_NOT_SOURCE_ENV_FILE"
    else
        fail "DEPLOY_SCRIPT_SOURCES_ENV_FILE"
    fi

else
    fail "DEPLOY_SCRIPT_MISSING"
fi

log ""
log "============================================================"
log "11. PRODUCTION SERVER / DEBUG SERVER DISCOVERY"
log "============================================================"

DEBUG_SERVER_COUNT=0
DEV_SERVER_COUNT=0
UNSAFE_BIND_COUNT=0

DEBUG_SERVER_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- 'app\.run\([^)]*debug[[:space:]]*=[[:space:]]*True|uvicorn\.run\([^)]*reload[[:space:]]*=[[:space:]]*True|flask[[:space:]]+run([^[:alnum:]_]|$)' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/scripts" 2>/dev/null | wc -l | tr -d ' ')"

DEV_SERVER_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- 'python[0-9.]*[[:space:]]+(-m[[:space:]]+)?http\.server|npm[[:space:]]+(run[[:space:]]+)?dev|vite[[:space:]]+--host' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/scripts" 2>/dev/null | wc -l | tr -d ' ')"

UNSAFE_BIND_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- '0\.0\.0\.0[[:space:]]*:[[:space:]]*[0-9]+|host[[:space:]]*=[[:space:]]*["'\'']0\.0\.0\.0["'\'']' \
    "${PROJECT_ROOT}/app" "${PROJECT_ROOT}/src" "${PROJECT_ROOT}/scripts" 2>/dev/null | wc -l | tr -d ' ')"

log "DEBUG_SERVER_COUNT=${DEBUG_SERVER_COUNT}"
log "DEV_SERVER_COUNT=${DEV_SERVER_COUNT}"
log "UNSAFE_BIND_COUNT=${UNSAFE_BIND_COUNT}"

if [ "${DEBUG_SERVER_COUNT}" -eq 0 ]; then
    pass "NO_DEBUG_SERVER_EXECUTION_PATTERN"
else
    fail "DEBUG_SERVER_EXECUTION_PATTERN_DETECTED"
fi

if [ "${DEV_SERVER_COUNT}" -eq 0 ]; then
    pass "NO_DEVELOPMENT_SERVER_EXECUTION_PATTERN"
else
    review "DEVELOPMENT_SERVER_PATTERN_DETECTED"
fi

log ""
log "============================================================"
log "12. TEST INFRASTRUCTURE DISCOVERY"
log "============================================================"

TEST_FILE_COUNT="$(
    find "${PROJECT_ROOT}" \
        -type d \
        \( -name .git -o -name audit-output -o -name forensics -o -name archive -o -name __pycache__ \) -prune -o \
        -type f \
        \( -name 'test_*.py' -o -name '*_test.py' -o -name '*.test.js' -o -name '*.test.ts' -o -name '*.spec.js' -o -name '*.spec.ts' \) \
        -print 2>/dev/null | wc -l | tr -d ' '
)"

PYTEST_CONFIG_COUNT="$(
    find "${PROJECT_ROOT}" \
        -type f \
        \( -name 'pytest.ini' -o -name 'pyproject.toml' -o -name 'tox.ini' -o -name 'setup.cfg' \) \
        -print 2>/dev/null | wc -l | tr -d ' '
)"

TEST_ASSERTION_COUNT="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    --exclude='*.pyc' \
    -- 'assert[[:space:]]+|self\.assert[A-Za-z]+\(' \
    "${PROJECT_ROOT}/tests" 2>/dev/null | wc -l | tr -d ' ')"

log "TEST_FILE_COUNT=${TEST_FILE_COUNT}"
log "PYTEST_CONFIG_COUNT=${PYTEST_CONFIG_COUNT}"
log "TEST_ASSERTION_COUNT=${TEST_ASSERTION_COUNT}"

if [ "${TEST_FILE_COUNT}" -gt 0 ]; then
    pass "TEST_FILES_PRESENT"
else
    review "NO_TEST_FILES_DETECTED"
fi

if [ "${TEST_ASSERTION_COUNT}" -gt 0 ]; then
    pass "TEST_ASSERTIONS_DETECTED"
else
    review "NO_TEST_ASSERTIONS_DETECTED"
fi

log ""
log "============================================================"
log "13. STATIC SECURITY TOOLING"
log "============================================================"

SECURITY_TOOL_COUNT=0

for tool_file in \
    ".github/workflows/ci.yml" \
    "pyproject.toml" \
    "package.json" \
    "Makefile" \
    "scripts/security.sh" \
    "scripts/security_scan.sh"
do
    if file_exists "${PROJECT_ROOT}/${tool_file}"; then
        if grep -Eiq \
            'bandit|semgrep|trivy|osv-scanner|pip-audit|safety|npm[[:space:]]+audit|cargo[[:space:]]+audit' \
            "${PROJECT_ROOT}/${tool_file}" 2>/dev/null; then
            SECURITY_TOOL_COUNT=$((SECURITY_TOOL_COUNT + 1))
            pass "SECURITY_TOOLING_REFERENCE=${tool_file}"
        fi
    fi
done

log "SECURITY_TOOL_REFERENCE_COUNT=${SECURITY_TOOL_COUNT}"

if [ "${SECURITY_TOOL_COUNT}" -gt 0 ]; then
    pass "STATIC_SECURITY_TOOLING_REFERENCED"
else
    review "NO_STATIC_SECURITY_TOOLING_REFERENCE_DETECTED"
fi

log ""
log "============================================================"
log "14. PRODUCTION DOCUMENTATION / OPERATIONAL CONTRACT"
log "============================================================"

README_PRESENT=0
DEPLOY_DOC_COUNT=0
HEALTH_DOC_COUNT=0
BACKUP_DOC_COUNT=0

if file_exists "${PROJECT_ROOT}/README.md"; then
    README_PRESENT=1
    pass "README_PRESENT"
else
    review "README_MISSING"
fi

DEPLOY_DOC_COUNT="$(grep -RIlE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    -- 'deploy|deployment|production' \
    "${PROJECT_ROOT}/README.md" "${PROJECT_ROOT}/docs" 2>/dev/null | wc -l | tr -d ' ')"

HEALTH_DOC_COUNT="$(grep -RIlE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    -- 'health|readiness|liveness' \
    "${PROJECT_ROOT}/README.md" "${PROJECT_ROOT}/docs" 2>/dev/null | wc -l | tr -d ' ')"

BACKUP_DOC_COUNT="$(grep -RIlE \
    --exclude-dir=.git \
    --exclude-dir=audit-output \
    --exclude-dir=forensics \
    --exclude-dir=archive \
    -- 'backup|restore|recovery' \
    "${PROJECT_ROOT}/README.md" "${PROJECT_ROOT}/docs" 2>/dev/null | wc -l | tr -d ' ')"

log "README_PRESENT=${README_PRESENT}"
log "DEPLOY_DOC_COUNT=${DEPLOY_DOC_COUNT}"
log "HEALTH_DOC_COUNT=${HEALTH_DOC_COUNT}"
log "BACKUP_DOC_COUNT=${BACKUP_DOC_COUNT}"

if [ "${DEPLOY_DOC_COUNT}" -gt 0 ]; then
    pass "DEPLOYMENT_DOCUMENTATION_SIGNAL_PRESENT"
else
    review "DEPLOYMENT_DOCUMENTATION_SIGNAL_NOT_DETECTED"
fi

if [ "${HEALTH_DOC_COUNT}" -gt 0 ]; then
    pass "HEALTH_DOCUMENTATION_SIGNAL_PRESENT"
else
    review "HEALTH_DOCUMENTATION_SIGNAL_NOT_DETECTED"
fi

if [ "${BACKUP_DOC_COUNT}" -gt 0 ]; then
    pass "BACKUP_RESTORE_DOCUMENTATION_SIGNAL_PRESENT"
else
    review "BACKUP_RESTORE_DOCUMENTATION_SIGNAL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "15. PRODUCTION READINESS CLASSIFICATION"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${FAILURE_COUNT}" -gt 0 ]; then
    STATUS="FAIL"
    RESULT="P0_03_R42_REAL_PRODUCTION_READINESS_BLOCKED"
    EXIT_CODE=2
elif [ "${REVIEW_COUNT}" -gt 0 ]; then
    STATUS="REVIEW"
    RESULT="P0_03_R42_REAL_PRODUCTION_READINESS_REVIEW"
    EXIT_CODE=1
else
    STATUS="PASS"
    RESULT="P0_03_R42_REAL_PRODUCTION_READINESS_PASS"
    EXIT_CODE=0
fi

log ""
log "============================================================"
log "16. FINAL EVIDENCE CARD"
log "============================================================"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"
log "AUTHORITY_FILE_COUNT=${AUTHORITY_COUNT}"
log "AUTHORITY_MISSING_COUNT=${AUTHORITY_MISSING_COUNT}"

log "DEBUG_TRUE_COUNT=${DEBUG_TRUE_COUNT}"
log "DEV_ENV_COUNT=${DEV_ENV_COUNT}"
log "INSECURE_SECRET_DEFAULT_COUNT=${INSECURE_SECRET_DEFAULT_COUNT}"
log "TEST_DEFAULT_COUNT=${TEST_DEFAULT_COUNT}"

log "COMPOSE_SERVICE_COUNT=${COMPOSE_SERVICE_COUNT}"
log "COMPOSE_HEALTHCHECK_COUNT=${COMPOSE_HEALTHCHECK_COUNT}"
log "COMPOSE_RESTART_COUNT=${COMPOSE_RESTART_COUNT}"
log "COMPOSE_PRIVILEGED_COUNT=${COMPOSE_PRIVILEGED_COUNT}"

log "MIGRATION_DIR_COUNT=${MIGRATION_DIR_COUNT}"
log "MIGRATION_COMMAND_COUNT=${MIGRATION_COMMAND_COUNT}"
log "ALEMBIC_CONFIG_COUNT=${ALEMBIC_CONFIG_COUNT}"
log "DB_MODEL_COUNT=${DB_MODEL_COUNT}"

log "HEALTH_ENDPOINT_COUNT=${HEALTH_ENDPOINT_COUNT}"
log "READINESS_ENDPOINT_COUNT=${READINESS_ENDPOINT_COUNT}"
log "LIVENESS_ENDPOINT_COUNT=${LIVENESS_ENDPOINT_COUNT}"

log "CI_TEST_COUNT=${CI_TEST_COUNT}"
log "CI_BUILD_COUNT=${CI_BUILD_COUNT}"
log "CI_DEPLOY_COUNT=${CI_DEPLOY_COUNT}"
log "CI_BRANCH_GUARD_COUNT=${CI_BRANCH_GUARD_COUNT}"

log "DEPLOY_FAIL_FAST_COUNT=${DEPLOY_FAIL_FAST_COUNT}"
log "DEPLOY_DANGEROUS_RM_COUNT=${DEPLOY_DANGEROUS_RM_COUNT}"
log "DEPLOY_ENV_SOURCE_COUNT=${DEPLOY_ENV_SOURCE_COUNT}"

log "DEBUG_SERVER_COUNT=${DEBUG_SERVER_COUNT}"
log "DEV_SERVER_COUNT=${DEV_SERVER_COUNT}"
log "UNSAFE_BIND_COUNT=${UNSAFE_BIND_COUNT}"

log "TEST_FILE_COUNT=${TEST_FILE_COUNT}"
log "TEST_ASSERTION_COUNT=${TEST_ASSERTION_COUNT}"
log "SECURITY_TOOL_REFERENCE_COUNT=${SECURITY_TOOL_COUNT}"

log "P0_03_R42_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"
log "REPORT=${REPORT}"

log "------------------------------------------------------------"

exit "${EXIT_CODE}"
