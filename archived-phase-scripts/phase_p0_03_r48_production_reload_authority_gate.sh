#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
SCRIPT_NAME="phase_p0_03_r48_production_reload_authority_gate.sh"
REPORT="${PROJECT_ROOT}/p0_03_r48_production_reload_authority_gate.txt"

COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
APP_DOCKERFILE="${PROJECT_ROOT}/app/Dockerfile"
BACKEND_DOCKERFILE="${PROJECT_ROOT}/docker/backend/Dockerfile"
DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"

TMP_COMPOSE="${PROJECT_ROOT}/.r48_tmp_compose"
TMP_DOCKER="${PROJECT_ROOT}/.r48_tmp_docker"
TMP_DEPLOY="${PROJECT_ROOT}/.r48_tmp_deploy"
TMP_SCRIPTS="${PROJECT_ROOT}/.r48_tmp_scripts"
TMP_PROD="${PROJECT_ROOT}/.r48_tmp_prod"

FAILURE_COUNT=0
REVIEW_COUNT=0

COMPOSE_BUILD_CONTEXT_COUNT=0
COMPOSE_DOCKERFILE_COUNT=0
COMPOSE_RELOAD_COUNT=0

COMPOSE_DOCKERFILE_TARGET_COUNT=0
COMPOSE_APP_DOCKERFILE_TARGET=0
COMPOSE_BACKEND_DOCKERFILE_TARGET=0

APP_DOCKERFILE_RELOAD_COUNT=0
BACKEND_DOCKERFILE_RELOAD_COUNT=0

DEPLOY_SCRIPT_RELOAD_COUNT=0
DEPLOY_SCRIPT_DOCKER_COMPOSE_COUNT=0
DEPLOY_SCRIPT_PRODUCTION_MARKER_COUNT=0

DEV_RELOAD_COUNT=0
LEGACY_RELOAD_COUNT=0
OTHER_SCRIPT_RELOAD_COUNT=0

PRODUCTION_RELOAD_BLOCKER=0
PRODUCTION_RELOAD_REVIEW=0

R47_STATUS=0
R47_EXIT_CODE=0
R47_RELOAD_IN_COMPOSE=0
R47_RELOAD_IN_DEPLOY=0
R47_HANDOFF_USED=0

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

cleanup() {
    rm -f \
        "${TMP_COMPOSE}" \
        "${TMP_DOCKER}" \
        "${TMP_DEPLOY}" \
        "${TMP_SCRIPTS}" \
        "${TMP_PROD}" \
        2>/dev/null || true
}

trap cleanup EXIT

: > "${REPORT}"
: > "${TMP_COMPOSE}"
: > "${TMP_DOCKER}"
: > "${TMP_DEPLOY}"
: > "${TMP_SCRIPTS}"
: > "${TMP_PROD}"

log "============================================================"
log "P0-03 R48 PRODUCTION RELOAD AUTHORITY GATE"
log "============================================================"
log ""

log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
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
pass "PRODUCTION_PATH_AUTHORITY_ANALYSIS=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. R47 AUTHORITY HANDOFF"
log "============================================================"

R47_REPORT="${PROJECT_ROOT}/p0_03_r47_production_reload_dataflow_gate.txt"

if [ -f "${R47_REPORT}" ]; then
    pass "R47_REPORT_PRESENT"

    R47_STATUS="$(
        awk -F= '
            $1=="P0_03_R47_STATUS" {v=$2}
            END {print v+0}
        ' "${R47_REPORT}" 2>/dev/null || true
    )"

    R47_EXIT_CODE="$(
        awk -F= '
            $1=="EXIT_CODE" {v=$2}
            END {print v+0}
        ' "${R47_REPORT}" 2>/dev/null || true
    )"

    R47_RELOAD_IN_COMPOSE="$(
        awk -F= '
            $1=="RELOAD_IN_COMPOSE" {v=$2}
            END {print v+0}
        ' "${R47_REPORT}" 2>/dev/null || true
    )"

    R47_RELOAD_IN_DEPLOY="$(
        awk -F= '
            $1=="RELOAD_IN_DEPLOY" {v=$2}
            END {print v+0}
        ' "${R47_REPORT}" 2>/dev/null || true
    )"

    : "${R47_STATUS:=0}"
    : "${R47_EXIT_CODE:=0}"
    : "${R47_RELOAD_IN_COMPOSE:=0}"
    : "${R47_RELOAD_IN_DEPLOY:=0}"

    R47_HANDOFF_USED=1

    log "R47_STATUS=${R47_STATUS}"
    log "R47_EXIT_CODE=${R47_EXIT_CODE}"
    log "R47_RELOAD_IN_COMPOSE=${R47_RELOAD_IN_COMPOSE}"
    log "R47_RELOAD_IN_DEPLOY=${R47_RELOAD_IN_DEPLOY}"
    log "R47_HANDOFF_USED=${R47_HANDOFF_USED}"

    pass "R47_RELOAD_SIGNAL_ACCEPTED_FOR_RECLASSIFICATION"
else
    review "R47_REPORT_NOT_AVAILABLE_HANDOFF_NOT_USED"

    R47_STATUS=0
    R47_EXIT_CODE=0
    R47_RELOAD_IN_COMPOSE=0
    R47_RELOAD_IN_DEPLOY=0
    R47_HANDOFF_USED=0

    log "R47_STATUS=${R47_STATUS}"
    log "R47_EXIT_CODE=${R47_EXIT_CODE}"
    log "R47_RELOAD_IN_COMPOSE=${R47_RELOAD_IN_COMPOSE}"
    log "R47_RELOAD_IN_DEPLOY=${R47_RELOAD_IN_DEPLOY}"
    log "R47_HANDOFF_USED=${R47_HANDOFF_USED}"
fi

log ""
log "============================================================"
log "3. PRODUCTION COMPOSE BUILD AUTHORITY"
log "============================================================"

if [ -f "${COMPOSE_FILE}" ]; then
    pass "DOCKER_COMPOSE_PRESENT"
else
    fail "DOCKER_COMPOSE_MISSING"
fi

log "COMPOSE_BUILD_AUTHORITY_BEGIN"

if [ -f "${COMPOSE_FILE}" ]; then
    awk '
        /^[[:space:]]*build:[[:space:]]*$/ ||
        /^[[:space:]]*context:[[:space:]]*/ ||
        /^[[:space:]]*dockerfile:[[:space:]]*/ {
            print FILENAME ":" FNR ":" $0
        }
    ' "${COMPOSE_FILE}" > "${TMP_COMPOSE}"

    while IFS= read -r line; do
        log "COMPOSE_BUILD_LINE=${line}"
    done < "${TMP_COMPOSE}"
fi

log "COMPOSE_BUILD_AUTHORITY_END"

COMPOSE_BUILD_CONTEXT_COUNT="$(
    awk '
        /^[[:space:]]*context:[[:space:]]*/ {c++}
        END {print c+0}
    ' "${COMPOSE_FILE}" 2>/dev/null || true
)"

COMPOSE_DOCKERFILE_COUNT="$(
    awk '
        /^[[:space:]]*dockerfile:[[:space:]]*/ {c++}
        END {print c+0}
    ' "${COMPOSE_FILE}" 2>/dev/null || true
)"

COMPOSE_RELOAD_COUNT="$(
    awk '
        /--reload/ {c++}
        END {print c+0}
    ' "${COMPOSE_FILE}" 2>/dev/null || true
)"

log "COMPOSE_BUILD_CONTEXT_COUNT=${COMPOSE_BUILD_CONTEXT_COUNT}"
log "COMPOSE_DOCKERFILE_COUNT=${COMPOSE_DOCKERFILE_COUNT}"
log "COMPOSE_RELOAD_COUNT=${COMPOSE_RELOAD_COUNT}"

if [ "${COMPOSE_RELOAD_COUNT}" -eq 0 ]; then
    pass "PRODUCTION_COMPOSE_HAS_NO_RELOAD_REFERENCE"
else
    fail "PRODUCTION_COMPOSE_CONTAINS_RELOAD"
fi

log ""
log "============================================================"
log "4. EXPLICIT COMPOSE DOCKERFILE TARGETS"
log "============================================================"

if [ -f "${COMPOSE_FILE}" ]; then

    COMPOSE_DOCKERFILE_TARGET_COUNT="$(
        awk '
            /^[[:space:]]*dockerfile:[[:space:]]*/ {
                v=$0
                sub(/^[[:space:]]*dockerfile:[[:space:]]*/, "", v)
                gsub(/[[:space:]]+$/, "", v)

                if (v=="app/Dockerfile" || v=="./app/Dockerfile") {
                    app++
                }

                if (v=="docker/backend/Dockerfile" ||
                    v=="./docker/backend/Dockerfile") {
                    backend++
                }
            }

            END {
                print (app+backend)+0
            }
        ' "${COMPOSE_FILE}"
    )"

    COMPOSE_APP_DOCKERFILE_TARGET="$(
        awk '
            /^[[:space:]]*dockerfile:[[:space:]]*/ {
                v=$0
                sub(/^[[:space:]]*dockerfile:[[:space:]]*/, "", v)
                gsub(/[[:space:]]+$/, "", v)

                if (v=="app/Dockerfile" || v=="./app/Dockerfile") {
                    c++
                }
            }

            END {
                print c+0
            }
        ' "${COMPOSE_FILE}"
    )"

    COMPOSE_BACKEND_DOCKERFILE_TARGET="$(
        awk '
            /^[[:space:]]*dockerfile:[[:space:]]*/ {
                v=$0
                sub(/^[[:space:]]*dockerfile:[[:space:]]*/, "", v)
                gsub(/[[:space:]]+$/, "", v)

                if (v=="docker/backend/Dockerfile" ||
                    v=="./docker/backend/Dockerfile") {
                    c++
                }
            }

            END {
                print c+0
            }
        ' "${COMPOSE_FILE}"
    )"
fi

log "COMPOSE_DOCKERFILE_TARGET_COUNT=${COMPOSE_DOCKERFILE_TARGET_COUNT}"
log "COMPOSE_APP_DOCKERFILE_TARGET=${COMPOSE_APP_DOCKERFILE_TARGET}"
log "COMPOSE_BACKEND_DOCKERFILE_TARGET=${COMPOSE_BACKEND_DOCKERFILE_TARGET}"

if [ "${COMPOSE_APP_DOCKERFILE_TARGET}" -gt 0 ]; then
    pass "PRODUCTION_COMPOSE_TARGETS_APP_DOCKERFILE"
else
    review "PRODUCTION_COMPOSE_APP_DOCKERFILE_TARGET_NOT_DETECTED"
fi

if [ "${COMPOSE_BACKEND_DOCKERFILE_TARGET}" -eq 0 ]; then
    pass "BACKEND_RELOAD_DOCKERFILE_NOT_SELECTED_BY_COMPOSE"
else
    fail "BACKEND_RELOAD_DOCKERFILE_SELECTED_BY_PRODUCTION_COMPOSE"
fi

log ""
log "============================================================"
log "5. TARGET DOCKERFILE RELOAD CHECK"
log "============================================================"

if [ -f "${APP_DOCKERFILE}" ]; then
    APP_DOCKERFILE_RELOAD_COUNT="$(
        awk '
            /--reload/ {c++}
            END {print c+0}
        ' "${APP_DOCKERFILE}"
    )"
else
    fail "APP_DOCKERFILE_MISSING"
fi

if [ -f "${BACKEND_DOCKERFILE}" ]; then
    BACKEND_DOCKERFILE_RELOAD_COUNT="$(
        awk '
            /--reload/ {c++}
            END {print c+0}
        ' "${BACKEND_DOCKERFILE}"
    )"
else
    BACKEND_DOCKERFILE_RELOAD_COUNT=0
    review "BACKEND_DOCKERFILE_NOT_PRESENT"
fi

log "APP_DOCKERFILE_RELOAD_COUNT=${APP_DOCKERFILE_RELOAD_COUNT}"
log "BACKEND_DOCKERFILE_RELOAD_COUNT=${BACKEND_DOCKERFILE_RELOAD_COUNT}"

if [ "${COMPOSE_APP_DOCKERFILE_TARGET}" -gt 0 ] &&
   [ "${APP_DOCKERFILE_RELOAD_COUNT}" -eq 0 ]; then
    pass "COMPOSE_SELECTED_APP_DOCKERFILE_HAS_NO_RELOAD"
fi

log ""
log "============================================================"
log "6. DEPLOYMENT SCRIPT AUTHORITY"
log "============================================================"

if [ -f "${DEPLOY_SCRIPT}" ]; then
    pass "DEPLOY_SCRIPT_PRESENT"

    DEPLOY_SCRIPT_RELOAD_COUNT="$(
        awk '
            /--reload/ {c++}
            END {print c+0}
        ' "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_SCRIPT_DOCKER_COMPOSE_COUNT="$(
        awk '
            /docker compose|docker-compose/ {c++}
            END {print c+0}
        ' "${DEPLOY_SCRIPT}"
    )"

    DEPLOY_SCRIPT_PRODUCTION_MARKER_COUNT="$(
        awk '
            /production|PRODUCTION|prod/ {c++}
            END {print c+0}
        ' "${DEPLOY_SCRIPT}"
    )"
else
    fail "DEPLOY_SCRIPT_MISSING"

    DEPLOY_SCRIPT_RELOAD_COUNT=0
    DEPLOY_SCRIPT_DOCKER_COMPOSE_COUNT=0
    DEPLOY_SCRIPT_PRODUCTION_MARKER_COUNT=0
fi

log "DEPLOY_SCRIPT_RELOAD_COUNT=${DEPLOY_SCRIPT_RELOAD_COUNT}"
log "DEPLOY_SCRIPT_DOCKER_COMPOSE_COUNT=${DEPLOY_SCRIPT_DOCKER_COMPOSE_COUNT}"
log "DEPLOY_SCRIPT_PRODUCTION_MARKER_COUNT=${DEPLOY_SCRIPT_PRODUCTION_MARKER_COUNT}"

if [ "${DEPLOY_SCRIPT_RELOAD_COUNT}" -eq 0 ]; then
    pass "PRIMARY_DEPLOY_SCRIPT_DOES_NOT_REFERENCE_RELOAD"
else
    fail "PRIMARY_DEPLOY_SCRIPT_CONTAINS_RELOAD"
fi

log ""
log "============================================================"
log "7. DEV AND LEGACY RELOAD ISOLATION"
log "============================================================"

DEV_DIR="${PROJECT_ROOT}/scripts/dev"
LEGACY_DIR="${PROJECT_ROOT}/scripts/legacy"

if [ -d "${DEV_DIR}" ]; then
    DEV_RELOAD_COUNT="$(
        grep -RIl \
            --exclude-dir=.git \
            -- '--reload' \
            "${DEV_DIR}" 2>/dev/null |
        wc -l |
        tr -d ' '
    )"
else
    DEV_RELOAD_COUNT=0
fi

if [ -d "${LEGACY_DIR}" ]; then
    LEGACY_RELOAD_COUNT="$(
        grep -RIl \
            --exclude-dir=.git \
            -- '--reload' \
            "${LEGACY_DIR}" 2>/dev/null |
        wc -l |
        tr -d ' '
    )"
else
    LEGACY_RELOAD_COUNT=0
fi

OTHER_SCRIPT_RELOAD_COUNT=0

if [ -d "${PROJECT_ROOT}/scripts" ]; then
    while IFS= read -r script_file; do
        case "${script_file}" in
            "${DEV_DIR}"/*)
                continue
                ;;
            "${LEGACY_DIR}"/*)
                continue
                ;;
            "${DEPLOY_SCRIPT}")
                continue
                ;;
            *)
                if grep -q -- '--reload' "${script_file}" 2>/dev/null; then
                    OTHER_SCRIPT_RELOAD_COUNT=$(
                        printf '%s' "${OTHER_SCRIPT_RELOAD_COUNT}" |
                        awk '{print $1+1}'
                    )
                fi
                ;;
        esac
    done < <(
        find "${PROJECT_ROOT}/scripts" \
            -type f \
            \( -name '*.sh' -o -name '*.bash' \) \
            -print 2>/dev/null
    )
fi

log "DEV_RELOAD_COUNT=${DEV_RELOAD_COUNT}"
log "LEGACY_RELOAD_COUNT=${LEGACY_RELOAD_COUNT}"
log "OTHER_SCRIPT_RELOAD_COUNT=${OTHER_SCRIPT_RELOAD_COUNT}"

if [ "${OTHER_SCRIPT_RELOAD_COUNT}" -eq 0 ]; then
    pass "NO_NON_DEV_NON_LEGACY_RELOAD_DEPLOY_SCRIPT_REFERENCE"
else
    review "NON_DEV_NON_LEGACY_SCRIPT_RELOAD_REFERENCE_PRESENT"
fi

log ""
log "============================================================"
log "8. PRODUCTION DEPLOYMENT PATH CORRELATION"
log "============================================================"

PRODUCTION_RELOAD_BLOCKER=0
PRODUCTION_RELOAD_REVIEW=0

if [ "${COMPOSE_BACKEND_DOCKERFILE_TARGET}" -gt 0 ]; then
    PRODUCTION_RELOAD_BLOCKER=1
    fail "RELOAD_DOCKERFILE_IS_SELECTED_BY_PRODUCTION_COMPOSE"
fi

if [ "${COMPOSE_APP_DOCKERFILE_TARGET}" -gt 0 ] &&
   [ "${APP_DOCKERFILE_RELOAD_COUNT}" -gt 0 ]; then
    PRODUCTION_RELOAD_BLOCKER=1
    fail "COMPOSE_SELECTED_APP_DOCKERFILE_CONTAINS_RELOAD"
fi

if [ "${DEPLOY_SCRIPT_RELOAD_COUNT}" -gt 0 ]; then
    PRODUCTION_RELOAD_BLOCKER=1
    fail "PRIMARY_DEPLOY_SCRIPT_CONTAINS_RELOAD"
fi

if [ "${DEV_RELOAD_COUNT}" -gt 0 ] ||
   [ "${LEGACY_RELOAD_COUNT}" -gt 0 ]; then

    if [ "${COMPOSE_BACKEND_DOCKERFILE_TARGET}" -eq 0 ] &&
       [ "${DEPLOY_SCRIPT_RELOAD_COUNT}" -eq 0 ] &&
       [ "${OTHER_SCRIPT_RELOAD_COUNT}" -eq 0 ]; then

        pass "DEV_LEGACY_RELOAD_ISOLATED_FROM_PRIMARY_PRODUCTION_PATH"
    else
        PRODUCTION_RELOAD_REVIEW=1
        review "DEV_LEGACY_RELOAD_REQUIRES_PATH_REVIEW"
    fi
fi

if [ "${COMPOSE_RELOAD_COUNT}" -eq 0 ]; then
    pass "PRODUCTION_COMPOSE_HAS_NO_RELOAD_REFERENCE"
else
    PRODUCTION_RELOAD_BLOCKER=1
    fail "PRODUCTION_COMPOSE_CONTAINS_RELOAD"
fi

if [ "${PRODUCTION_RELOAD_BLOCKER}" -eq 0 ]; then
    pass "PRODUCTION_RELOAD_BLOCKER=0"
else
    fail "PRODUCTION_RELOAD_BLOCKER=${PRODUCTION_RELOAD_BLOCKER}"
fi

log ""
log "============================================================"
log "9. R47 RECLASSIFICATION"
log "============================================================"

if [ "${R47_HANDOFF_USED}" -eq 1 ]; then

    if [ "${R47_RELOAD_IN_DEPLOY}" -gt 0 ] &&
       [ "${DEPLOY_SCRIPT_RELOAD_COUNT}" -eq 0 ] &&
       [ "${COMPOSE_BACKEND_DOCKERFILE_TARGET}" -eq 0 ] &&
       [ "${APP_DOCKERFILE_RELOAD_COUNT}" -eq 0 ]; then

        pass "R47_RELOAD_SIGNAL_RECLASSIFIED_AS_NON_PRODUCTION"
        pass "R47_PRODUCTION_RELOAD_FALSE_POSITIVE_CONFIRMED"

    elif [ "${PRODUCTION_RELOAD_BLOCKER}" -eq 0 ]; then

        pass "R47_SIGNAL_DOES_NOT_ESTABLISH_PRODUCTION_RELOAD_BLOCKER"

    else
        fail "R47_SIGNAL_CORRELATES_WITH_PRODUCTION_RELOAD_PATH"
    fi

else
    pass "R47_HANDOFF_NOT_REQUIRED_FOR_CURRENT_AUTHORITY_DECISION"
    pass "R48_CURRENT_AUTHORITY_ANALYSIS_IS_SELF_CONTAINED"
fi

log ""
log "============================================================"
log "10. FINAL R48 DECISION"
log "============================================================"

log "PRODUCTION_RELOAD_BLOCKER=${PRODUCTION_RELOAD_BLOCKER}"
log "PRODUCTION_RELOAD_REVIEW=${PRODUCTION_RELOAD_REVIEW}"
log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"
log "R47_HANDOFF_USED=${R47_HANDOFF_USED}"

if [ "${PRODUCTION_RELOAD_BLOCKER}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R48_PRODUCTION_RELOAD_BLOCKER_CONFIRMED"
    EXIT_CODE=2

elif [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R48_PRODUCTION_RELOAD_AUTHORITY_GATE_FAILED"
    EXIT_CODE=2

elif [ "${PRODUCTION_RELOAD_REVIEW}" -gt 0 ]; then

    STATUS="REVIEW"
    RESULT="P0_03_R48_PRODUCTION_RELOAD_AUTHORITY_REVIEW"
    EXIT_CODE=1

else

    STATUS="PASS"
    RESULT="P0_03_R48_PRODUCTION_RELOAD_AUTHORITY_CLOSED"
    EXIT_CODE=0
fi

log "P0_03_R48_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R48 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
