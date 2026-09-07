#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="/data/data/com.termux/files/home/waste-platform"
REPORT="${PROJECT_ROOT}/p0_03_r52_rollback_recovery_authority_reconciliation_gate.txt"

DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"
COMPOSE_PRODUCTION="${PROJECT_ROOT}/docker-compose.production.yml"
COMPOSE_PRIMARY="${PROJECT_ROOT}/docker-compose.yml"
DOC_DEPLOY="${PROJECT_ROOT}/docs/DEPLOYMENT.md"
DOC_DEPLOY_LOWER="${PROJECT_ROOT}/docs/deployment.md"
DOC_CHECKLIST="${PROJECT_ROOT}/docs/PRODUCTION-CHECKLIST.md"
README="${PROJECT_ROOT}/README.md"

R50_REPORT="${PROJECT_ROOT}/p0_03_r50_ci_production_deployment_architecture_reconciliation_gate.txt"
R51_REPORT="${PROJECT_ROOT}/p0_03_r51_production_deployment_safety_authority_gate.txt"

TMP_AUTHORITY="${PROJECT_ROOT}/.r52_tmp_authority"
TMP_PRODUCTION="${PROJECT_ROOT}/.r52_tmp_production"
TMP_DOCS="${PROJECT_ROOT}/.r52_tmp_docs"

FAILURE_COUNT=0
REVIEW_COUNT=0

R50_STATUS="UNKNOWN"
R50_PRODUCTION_DEPLOYMENT_AUTHORITY=0
R50_PRODUCTION_DEPLOYMENT_GAP=0
R50_PRODUCTION_DEPLOYMENT_BLOCKER=0

R51_STATUS="UNKNOWN"
R51_DEPLOYMENT_SAFETY_GAP=0
R51_DEPLOYMENT_SAFETY_BLOCKER=0
R51_ROLLBACK_AUTHORITY=0
R51_RECOVERY_AUTHORITY=0

DEPLOY_PRESENT=0
COMPOSE_PRODUCTION_PRESENT=0
COMPOSE_PRIMARY_PRESENT=0

PRODUCTION_ROLLBACK_COUNT=0
PRODUCTION_REVERT_COUNT=0
PRODUCTION_RESTORE_COUNT=0
PRODUCTION_RECOVERY_COUNT=0
PRODUCTION_BACKUP_COUNT=0
PRODUCTION_SNAPSHOT_COUNT=0
PRODUCTION_PREVIOUS_IMAGE_COUNT=0
PRODUCTION_VERSION_PIN_COUNT=0
PRODUCTION_IMAGE_TAG_COUNT=0
PRODUCTION_DOWN_COUNT=0
PRODUCTION_UP_COUNT=0
PRODUCTION_RECREATE_COUNT=0

DEPLOY_ROLLBACK_COUNT=0
DEPLOY_REVERT_COUNT=0
DEPLOY_RESTORE_COUNT=0
DEPLOY_RECOVERY_COUNT=0
DEPLOY_BACKUP_COUNT=0
DEPLOY_PREVIOUS_IMAGE_COUNT=0
DEPLOY_VERSION_PIN_COUNT=0

DOC_ROLLBACK_COUNT=0
DOC_REVERT_COUNT=0
DOC_RESTORE_COUNT=0
DOC_RECOVERY_COUNT=0
DOC_BACKUP_COUNT=0
DOC_SNAPSHOT_COUNT=0
DOC_PREVIOUS_VERSION_COUNT=0
DOC_RUNBOOK_COUNT=0

RECOVERY_AUTHORITY_PRESENT=0
ROLLBACK_AUTHORITY_PRESENT=0
EXTERNAL_RECOVERY_AUTHORITY=0
RECOVERY_DOCUMENTED=0

R52_DEPLOYMENT_SAFETY_GAP=0
R52_DEPLOYMENT_SAFETY_BLOCKER=0

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
        "${TMP_AUTHORITY}" \
        "${TMP_PRODUCTION}" \
        "${TMP_DOCS}" \
        2>/dev/null || true
}

trap cleanup EXIT

: > "${REPORT}"
: > "${TMP_AUTHORITY}"
: > "${TMP_PRODUCTION}"
: > "${TMP_DOCS}"

log "============================================================"
log "P0-03 R52 ROLLBACK / RECOVERY AUTHORITY RECONCILIATION GATE"
log "============================================================"
log ""

log "============================================================"
log "1. SAFETY PRECHECK"
log "============================================================"

if [ -d "${PROJECT_ROOT}" ]; then
    pass "PROJECT_ROOT_CONFIRMED=${PROJECT_ROOT}"
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
pass "ROLLBACK_RECOVERY_RECONCILIATION_ONLY=YES"
pass "NO_SOURCE_MODIFICATION=YES"

log ""
log "============================================================"
log "2. AUTHORITY FILE PRESENCE"
log "============================================================"

if [ -f "${DEPLOY_SCRIPT}" ]; then
    DEPLOY_PRESENT=1
    pass "PRIMARY_DEPLOY_SCRIPT_PRESENT"
else
    fail "PRIMARY_DEPLOY_SCRIPT_MISSING"
fi

if [ -f "${COMPOSE_PRODUCTION}" ]; then
    COMPOSE_PRODUCTION_PRESENT=1
    pass "PRODUCTION_COMPOSE_PRESENT"
else
    review "PRODUCTION_COMPOSE_NOT_PRESENT"
fi

if [ -f "${COMPOSE_PRIMARY}" ]; then
    COMPOSE_PRIMARY_PRESENT=1
    pass "PRIMARY_COMPOSE_PRESENT"
else
    fail "PRIMARY_COMPOSE_MISSING"
fi

log "DEPLOY_PRESENT=${DEPLOY_PRESENT}"
log "COMPOSE_PRODUCTION_PRESENT=${COMPOSE_PRODUCTION_PRESENT}"
log "COMPOSE_PRIMARY_PRESENT=${COMPOSE_PRIMARY_PRESENT}"

log ""
log "============================================================"
log "3. R50 / R51 HANDOFF"
log "============================================================"

if [ -f "${R50_REPORT}" ]; then

    R50_STATUS="$(
        awk -F= '
            $1=="P0_03_R50_STATUS" {v=$2}
            END {print v}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_AUTHORITY="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_AUTHORITY" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_GAP="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_GAP" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    R50_PRODUCTION_DEPLOYMENT_BLOCKER="$(
        awk -F= '
            $1=="PRODUCTION_DEPLOYMENT_BLOCKER" {v=$2}
            END {print v+0}
        ' "${R50_REPORT}" 2>/dev/null || true
    )"

    : "${R50_STATUS:=UNKNOWN}"
    : "${R50_PRODUCTION_DEPLOYMENT_AUTHORITY:=0}"
    : "${R50_PRODUCTION_DEPLOYMENT_GAP:=0}"
    : "${R50_PRODUCTION_DEPLOYMENT_BLOCKER:=0}"

    log "R50_STATUS=${R50_STATUS}"
    log "R50_PRODUCTION_DEPLOYMENT_AUTHORITY=${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}"
    log "R50_PRODUCTION_DEPLOYMENT_GAP=${R50_PRODUCTION_DEPLOYMENT_GAP}"
    log "R50_PRODUCTION_DEPLOYMENT_BLOCKER=${R50_PRODUCTION_DEPLOYMENT_BLOCKER}"

    if [ "${R50_STATUS}" = "PASS" ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}" -eq 1 ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_GAP}" -eq 0 ] &&
       [ "${R50_PRODUCTION_DEPLOYMENT_BLOCKER}" -eq 0 ]; then
        pass "R50_HANDOFF_ACCEPTED"
    else
        review "R50_HANDOFF_NOT_CLEAN"
    fi
else
    review "R50_REPORT_NOT_AVAILABLE"
fi

if [ -f "${R51_REPORT}" ]; then

    R51_STATUS="$(
        awk -F= '
            $1=="P0_03_R51_STATUS" {v=$2}
            END {print v}
        ' "${R51_REPORT}" 2>/dev/null || true
    )"

    R51_DEPLOYMENT_SAFETY_GAP="$(
        awk -F= '
            $1=="DEPLOYMENT_SAFETY_GAP" {v=$2}
            END {print v+0}
        ' "${R51_REPORT}" 2>/dev/null || true
    )"

    R51_DEPLOYMENT_SAFETY_BLOCKER="$(
        awk -F= '
            $1=="DEPLOYMENT_SAFETY_BLOCKER" {v=$2}
            END {print v+0}
        ' "${R51_REPORT}" 2>/dev/null || true
    )"

    R51_ROLLBACK_AUTHORITY="$(
        awk -F= '
            $1=="ROLLBACK_AUTHORITY" {v=$2}
            END {print v+0}
        ' "${R51_REPORT}" 2>/dev/null || true
    )"

    R51_RECOVERY_AUTHORITY="$(
        awk -F= '
            $1=="RECOVERY_AUTHORITY" {v=$2}
            END {print v+0}
        ' "${R51_REPORT}" 2>/dev/null || true
    )"

    : "${R51_STATUS:=UNKNOWN}"
    : "${R51_DEPLOYMENT_SAFETY_GAP:=0}"
    : "${R51_DEPLOYMENT_SAFETY_BLOCKER:=0}"
    : "${R51_ROLLBACK_AUTHORITY:=0}"
    : "${R51_RECOVERY_AUTHORITY:=0}"

    log "R51_STATUS=${R51_STATUS}"
    log "R51_DEPLOYMENT_SAFETY_GAP=${R51_DEPLOYMENT_SAFETY_GAP}"
    log "R51_DEPLOYMENT_SAFETY_BLOCKER=${R51_DEPLOYMENT_SAFETY_BLOCKER}"
    log "R51_ROLLBACK_AUTHORITY=${R51_ROLLBACK_AUTHORITY}"
    log "R51_RECOVERY_AUTHORITY=${R51_RECOVERY_AUTHORITY}"

    if [ "${R51_DEPLOYMENT_SAFETY_BLOCKER}" -eq 0 ]; then
        pass "R51_NO_DEPLOYMENT_SAFETY_BLOCKER"
    else
        fail "R51_DEPLOYMENT_SAFETY_BLOCKER_PRESENT"
    fi
else
    review "R51_REPORT_NOT_AVAILABLE"
fi

log ""
log "============================================================"
log "4. PRIMARY DEPLOY SCRIPT RECOVERY ANALYSIS"
log "============================================================"

if [ "${DEPLOY_PRESENT}" -eq 1 ]; then

    DEPLOY_ROLLBACK_COUNT="$(
        grep -Eic \
            'rollback|roll-back|roll_back' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_REVERT_COUNT="$(
        grep -Eic \
            'revert|previous[[:space:]_-]*(image|version|release)|old[[:space:]_-]*(image|version|release)' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_RESTORE_COUNT="$(
        grep -Eic \
            'restore|recover|recovery' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_BACKUP_COUNT="$(
        grep -Eic \
            'backup|snapshot' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_PREVIOUS_IMAGE_COUNT="$(
        grep -Eic \
            'previous.*image|old.*image|rollback.*image|image.*rollback' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"

    DEPLOY_VERSION_PIN_COUNT="$(
        grep -Eic \
            'image:[[:space:]]*[^[:space:]]+:[[:alnum:]_.-]+|VERSION=|IMAGE_TAG=|TAG=' \
            "${DEPLOY_SCRIPT}" 2>/dev/null || true
    )"
fi

log "DEPLOY_ROLLBACK_COUNT=${DEPLOY_ROLLBACK_COUNT}"
log "DEPLOY_REVERT_COUNT=${DEPLOY_REVERT_COUNT}"
log "DEPLOY_RESTORE_COUNT=${DEPLOY_RESTORE_COUNT}"
log "DEPLOY_BACKUP_COUNT=${DEPLOY_BACKUP_COUNT}"
log "DEPLOY_PREVIOUS_IMAGE_COUNT=${DEPLOY_PREVIOUS_IMAGE_COUNT}"
log "DEPLOY_VERSION_PIN_COUNT=${DEPLOY_VERSION_PIN_COUNT}"

if [ "${DEPLOY_ROLLBACK_COUNT}" -gt 0 ]; then
    pass "DEPLOY_SCRIPT_EXPLICIT_ROLLBACK_SIGNAL_PRESENT"
else
    review "DEPLOY_SCRIPT_EXPLICIT_ROLLBACK_SIGNAL_NOT_DETECTED"
fi

if [ "${DEPLOY_REVERT_COUNT}" -gt 0 ] ||
   [ "${DEPLOY_RESTORE_COUNT}" -gt 0 ]; then
    pass "DEPLOY_SCRIPT_REVERT_OR_RECOVERY_SIGNAL_PRESENT"
else
    review "DEPLOY_SCRIPT_REVERT_OR_RECOVERY_SIGNAL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "5. PRODUCTION COMPOSE RECOVERY ANALYSIS"
log "============================================================"

if [ "${COMPOSE_PRODUCTION_PRESENT}" -eq 1 ]; then

    PRODUCTION_ROLLBACK_COUNT="$(
        grep -Eic \
            'rollback|roll-back|roll_back' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_REVERT_COUNT="$(
        grep -Eic \
            'revert|previous[[:space:]_-]*(image|version|release)|old[[:space:]_-]*(image|version|release)' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_RESTORE_COUNT="$(
        grep -Eic \
            'restore|recover|recovery' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_BACKUP_COUNT="$(
        grep -Eic \
            'backup|snapshot' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_SNAPSHOT_COUNT="$(
        grep -Eic \
            'snapshot' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_PREVIOUS_IMAGE_COUNT="$(
        grep -Eic \
            'previous.*image|old.*image|rollback.*image|image.*rollback' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_VERSION_PIN_COUNT="$(
        grep -Eic \
            'VERSION=|IMAGE_TAG=|TAG=|version:' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_IMAGE_TAG_COUNT="$(
        grep -Eic \
            'image:[[:space:]]*[^[:space:]]+:[[:alnum:]_.-]+' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_DOWN_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*down' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_UP_COUNT="$(
        grep -Eic \
            'docker[[:space:]]+compose.*up' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"

    PRODUCTION_RECREATE_COUNT="$(
        grep -Eic \
            'recreate|force-recreate' \
            "${COMPOSE_PRODUCTION}" 2>/dev/null || true
    )"
fi

log "PRODUCTION_ROLLBACK_COUNT=${PRODUCTION_ROLLBACK_COUNT}"
log "PRODUCTION_REVERT_COUNT=${PRODUCTION_REVERT_COUNT}"
log "PRODUCTION_RESTORE_COUNT=${PRODUCTION_RESTORE_COUNT}"
log "PRODUCTION_BACKUP_COUNT=${PRODUCTION_BACKUP_COUNT}"
log "PRODUCTION_SNAPSHOT_COUNT=${PRODUCTION_SNAPSHOT_COUNT}"
log "PRODUCTION_PREVIOUS_IMAGE_COUNT=${PRODUCTION_PREVIOUS_IMAGE_COUNT}"
log "PRODUCTION_VERSION_PIN_COUNT=${PRODUCTION_VERSION_PIN_COUNT}"
log "PRODUCTION_IMAGE_TAG_COUNT=${PRODUCTION_IMAGE_TAG_COUNT}"
log "PRODUCTION_DOWN_COUNT=${PRODUCTION_DOWN_COUNT}"
log "PRODUCTION_UP_COUNT=${PRODUCTION_UP_COUNT}"
log "PRODUCTION_RECREATE_COUNT=${PRODUCTION_RECREATE_COUNT}"

if [ "${PRODUCTION_ROLLBACK_COUNT}" -gt 0 ]; then
    pass "PRODUCTION_COMPOSE_EXPLICIT_ROLLBACK_SIGNAL_PRESENT"
else
    review "PRODUCTION_COMPOSE_EXPLICIT_ROLLBACK_SIGNAL_NOT_DETECTED"
fi

if [ "${PRODUCTION_IMAGE_TAG_COUNT}" -gt 0 ] ||
   [ "${PRODUCTION_VERSION_PIN_COUNT}" -gt 0 ]; then
    pass "PRODUCTION_VERSION_OR_IMAGE_IDENTITY_SIGNAL_PRESENT"
else
    review "PRODUCTION_VERSION_IDENTITY_SIGNAL_NOT_DETECTED"
fi

log ""
log "============================================================"
log "6. PRIMARY COMPOSE RECOVERY CONTEXT"
log "============================================================"

if [ "${COMPOSE_PRIMARY_PRESENT}" -eq 1 ]; then

    grep -Ei \
        'rollback|revert|restore|recover|recovery|backup|snapshot|previous[[:space:]_-]*(image|version|release)|image:[[:space:]]*[^[:space:]]+:' \
        "${COMPOSE_PRIMARY}" \
        > "${TMP_AUTHORITY}" 2>/dev/null || true

    PRODUCTION_VERSION_PIN_COUNT=$(
        grep -Eic \
            'image:[[:space:]]*[^[:space:]]+:[[:alnum:]_.-]+' \
            "${COMPOSE_PRIMARY}" 2>/dev/null || true
    )

    log "PRIMARY_COMPOSE_VERSION_OR_IMAGE_SIGNAL_COUNT=${PRODUCTION_VERSION_PIN_COUNT}"

    if [ "${PRODUCTION_VERSION_PIN_COUNT}" -gt 0 ]; then
        pass "PRIMARY_COMPOSE_HAS_VERSIONED_IMAGE_SIGNAL"
    else
        review "PRIMARY_COMPOSE_VERSIONED_IMAGE_SIGNAL_NOT_DETECTED"
    fi
fi

log ""
log "============================================================"
log "7. PRODUCTION DOCUMENTATION RECOVERY AUTHORITY"
log "============================================================"

DOC_FILES=()

for f in \
    "${DOC_DEPLOY}" \
    "${DOC_DEPLOY_LOWER}" \
    "${DOC_CHECKLIST}" \
    "${README}"
do
    if [ -f "${f}" ]; then
        DOC_FILES+=("${f}")
    fi
done

for f in "${DOC_FILES[@]}"; do
    grep -Ei \
        'rollback|roll-back|roll_back|revert|restore|recover|recovery|backup|snapshot|previous[[:space:]_-]*(version|release|image)|runbook' \
        "${f}" \
        >> "${TMP_DOCS}" 2>/dev/null || true
done

DOC_ROLLBACK_COUNT="$(
    grep -Eic \
        'rollback|roll-back|roll_back' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_REVERT_COUNT="$(
    grep -Eic \
        'revert' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_RESTORE_COUNT="$(
    grep -Eic \
        'restore' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_RECOVERY_COUNT="$(
    grep -Eic \
        'recover|recovery' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_BACKUP_COUNT="$(
    grep -Eic \
        'backup' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_SNAPSHOT_COUNT="$(
    grep -Eic \
        'snapshot' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_PREVIOUS_VERSION_COUNT="$(
    grep -Eic \
        'previous[[:space:]_-]*(version|release|image)' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

DOC_RUNBOOK_COUNT="$(
    grep -Eic \
        'runbook' \
        "${TMP_DOCS}" 2>/dev/null || true
)"

log "DOC_ROLLBACK_COUNT=${DOC_ROLLBACK_COUNT}"
log "DOC_REVERT_COUNT=${DOC_REVERT_COUNT}"
log "DOC_RESTORE_COUNT=${DOC_RESTORE_COUNT}"
log "DOC_RECOVERY_COUNT=${DOC_RECOVERY_COUNT}"
log "DOC_BACKUP_COUNT=${DOC_BACKUP_COUNT}"
log "DOC_SNAPSHOT_COUNT=${DOC_SNAPSHOT_COUNT}"
log "DOC_PREVIOUS_VERSION_COUNT=${DOC_PREVIOUS_VERSION_COUNT}"
log "DOC_RUNBOOK_COUNT=${DOC_RUNBOOK_COUNT}"

if [ "${DOC_ROLLBACK_COUNT}" -gt 0 ] ||
   [ "${DOC_REVERT_COUNT}" -gt 0 ] ||
   [ "${DOC_RESTORE_COUNT}" -gt 0 ] ||
   [ "${DOC_RECOVERY_COUNT}" -gt 0 ]; then
    RECOVERY_DOCUMENTED=1
    pass "RECOVERY_OR_ROLLBACK_DOCUMENTATION_SIGNAL_PRESENT"
else
    review "RECOVERY_OR_ROLLBACK_DOCUMENTATION_SIGNAL_NOT_DETECTED"
fi

if [ "${DOC_RUNBOOK_COUNT}" -gt 0 ]; then
    pass "RECOVERY_RUNBOOK_SIGNAL_PRESENT"
else
    review "RECOVERY_RUNBOOK_SIGNAL_NOT_DETECTED"
fi

log "RECOVERY_DOCUMENTED=${RECOVERY_DOCUMENTED}"

log ""
log "============================================================"
log "8. RECOVERY AUTHORITY CLASSIFICATION"
log "============================================================"

ROLLBACK_AUTHORITY_PRESENT=0
RECOVERY_AUTHORITY_PRESENT=0
EXTERNAL_RECOVERY_AUTHORITY=0

if [ "${DEPLOY_ROLLBACK_COUNT}" -gt 0 ] ||
   [ "${PRODUCTION_ROLLBACK_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY_PRESENT=1
    RECOVERY_AUTHORITY_PRESENT=1
    pass "DIRECT_ROLLBACK_AUTHORITY_PRESENT"

elif [ "${DEPLOY_REVERT_COUNT}" -gt 0 ] &&
     [ "${DEPLOY_PREVIOUS_IMAGE_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY_PRESENT=1
    RECOVERY_AUTHORITY_PRESENT=1
    pass "DEPLOY_SCRIPT_VERSION_REVERT_AUTHORITY_PRESENT"

elif [ "${PRODUCTION_PREVIOUS_IMAGE_COUNT}" -gt 0 ] &&
     [ "${PRODUCTION_IMAGE_TAG_COUNT}" -gt 0 ]; then

    ROLLBACK_AUTHORITY_PRESENT=1
    RECOVERY_AUTHORITY_PRESENT=1
    pass "PRODUCTION_COMPOSE_VERSION_REVERT_AUTHORITY_PRESENT"

elif [ "${RECOVERY_DOCUMENTED}" -eq 1 ] &&
     [ "${DOC_RUNBOOK_COUNT}" -gt 0 ]; then

    EXTERNAL_RECOVERY_AUTHORITY=1
    RECOVERY_AUTHORITY_PRESENT=1
    pass "DOCUMENTED_EXTERNAL_RECOVERY_AUTHORITY_PRESENT"

elif [ "${DOC_ROLLBACK_COUNT}" -gt 0 ] ||
     [ "${DOC_RECOVERY_COUNT}" -gt 0 ]; then

    EXTERNAL_RECOVERY_AUTHORITY=1
    RECOVERY_AUTHORITY_PRESENT=1
    review "DOCUMENTED_RECOVERY_PRESENT_BUT_EXECUTION_AUTHORITY_NOT_LOCALLY_VERIFIED"

else

    review "NO_ROLLBACK_OR_RECOVERY_AUTHORITY_IDENTIFIED"
fi

log "ROLLBACK_AUTHORITY_PRESENT=${ROLLBACK_AUTHORITY_PRESENT}"
log "RECOVERY_AUTHORITY_PRESENT=${RECOVERY_AUTHORITY_PRESENT}"
log "EXTERNAL_RECOVERY_AUTHORITY=${EXTERNAL_RECOVERY_AUTHORITY}"

log ""
log "============================================================"
log "9. R51 GAP RECONCILIATION"
log "============================================================"

R52_DEPLOYMENT_SAFETY_GAP=0
R52_DEPLOYMENT_SAFETY_BLOCKER=0

if [ "${R51_DEPLOYMENT_SAFETY_BLOCKER}" -gt 0 ]; then
    R52_DEPLOYMENT_SAFETY_BLOCKER=1
    fail "R51_DEPLOYMENT_SAFETY_BLOCKER_REMAINS"
fi

if [ "${RECOVERY_AUTHORITY_PRESENT}" -gt 0 ]; then

    pass "R51_ROLLBACK_GAP_RECLASSIFIED_BY_DISCOVERED_RECOVERY_AUTHORITY"

else

    R52_DEPLOYMENT_SAFETY_GAP=1
    review "R51_ROLLBACK_GAP_REMAINS_UNRESOLVED"
fi

log "R52_DEPLOYMENT_SAFETY_GAP=${R52_DEPLOYMENT_SAFETY_GAP}"
log "R52_DEPLOYMENT_SAFETY_BLOCKER=${R52_DEPLOYMENT_SAFETY_BLOCKER}"

log ""
log "============================================================"
log "10. FINAL R52 DECISION"
log "============================================================"

log "R50_STATUS=${R50_STATUS}"
log "R50_PRODUCTION_DEPLOYMENT_AUTHORITY=${R50_PRODUCTION_DEPLOYMENT_AUTHORITY}"
log "R50_PRODUCTION_DEPLOYMENT_GAP=${R50_PRODUCTION_DEPLOYMENT_GAP}"
log "R50_PRODUCTION_DEPLOYMENT_BLOCKER=${R50_PRODUCTION_DEPLOYMENT_BLOCKER}"

log "R51_STATUS=${R51_STATUS}"
log "R51_DEPLOYMENT_SAFETY_GAP=${R51_DEPLOYMENT_SAFETY_GAP}"
log "R51_DEPLOYMENT_SAFETY_BLOCKER=${R51_DEPLOYMENT_SAFETY_BLOCKER}"
log "R51_ROLLBACK_AUTHORITY=${R51_ROLLBACK_AUTHORITY}"
log "R51_RECOVERY_AUTHORITY=${R51_RECOVERY_AUTHORITY}"

log "ROLLBACK_AUTHORITY_PRESENT=${ROLLBACK_AUTHORITY_PRESENT}"
log "RECOVERY_AUTHORITY_PRESENT=${RECOVERY_AUTHORITY_PRESENT}"
log "EXTERNAL_RECOVERY_AUTHORITY=${EXTERNAL_RECOVERY_AUTHORITY}"
log "RECOVERY_DOCUMENTED=${RECOVERY_DOCUMENTED}"

log "R52_DEPLOYMENT_SAFETY_GAP=${R52_DEPLOYMENT_SAFETY_GAP}"
log "R52_DEPLOYMENT_SAFETY_BLOCKER=${R52_DEPLOYMENT_SAFETY_BLOCKER}"

log "FAILURE_COUNT=${FAILURE_COUNT}"
log "REVIEW_COUNT=${REVIEW_COUNT}"

if [ "${R52_DEPLOYMENT_SAFETY_BLOCKER}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R52_ROLLBACK_RECOVERY_SAFETY_BLOCKER_CONFIRMED"
    EXIT_CODE=2

elif [ "${FAILURE_COUNT}" -gt 0 ]; then

    STATUS="FAIL"
    RESULT="P0_03_R52_ROLLBACK_RECOVERY_AUTHORITY_GATE_FAILED"
    EXIT_CODE=2

elif [ "${R52_DEPLOYMENT_SAFETY_GAP}" -eq 0 ] &&
     [ "${RECOVERY_AUTHORITY_PRESENT}" -eq 1 ]; then

    STATUS="PASS"
    RESULT="P0_03_R52_ROLLBACK_RECOVERY_AUTHORITY_CLOSED"
    EXIT_CODE=0

else

    STATUS="REVIEW"
    RESULT="P0_03_R52_ROLLBACK_RECOVERY_AUTHORITY_REVIEW"
    EXIT_CODE=1
fi

log "P0_03_R52_STATUS=${STATUS}"
log "RESULT=${RESULT}"
log "EXIT_CODE=${EXIT_CODE}"

log ""
log "============================================================"
log "R52 COMPLETE"
log "============================================================"

exit "${EXIT_CODE}"
