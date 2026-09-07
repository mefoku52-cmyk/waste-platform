#!/usr/bin/env bash

set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
REPORT="audit-output/p0_02_safety_signed_production_remediation_preflight.txt"

FAILURE_COUNT=0
REVIEW_COUNT=0
CHECK_COUNT=0

pass() {
    echo "PASS: $1" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $1" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $1" | tee -a "$REPORT"
}

check() {
    CHECK_COUNT=$((CHECK_COUNT + 1))
}

section() {
    echo | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
    echo "$1" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

: > "$REPORT"

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

section "2. REQUIRED PRODUCTION AUTHORITY"

REQUIRED_PATHS=(
    "app"
    "apps/web"
    "docker/nginx/Dockerfile"
    "docker-compose.yml"
    "scripts/deploy.sh"
    ".github/workflows/ci.yml"
    ".env.production"
)

for path in "${REQUIRED_PATHS[@]}"; do
    check

    if [ -e "$path" ]; then
        pass "REQUIRED_AUTHORITY_PRESENT=$path"
    else
        fail "REQUIRED_AUTHORITY_MISSING=$path"
    fi
done

section "3. FORBIDDEN SCAN SURFACES"

FORBIDDEN_PATHS=(
    ".git"
    "audit-output"
    "node_modules"
    ".next"
    "dist"
    "build"
    "__pycache__"
    "_quarantine"
    "scripts/forensics/archive"
)

for path in "${FORBIDDEN_PATHS[@]}"; do
    if [ -e "$path" ]; then
        echo "EXCLUDED_SCAN_SURFACE=$path" | tee -a "$REPORT"
    else
        echo "ABSENT_SCAN_SURFACE=$path" | tee -a "$REPORT"
    fi
done

pass "FORBIDDEN_SCAN_SURFACES_EXPLICITLY_EXCLUDED"

section "4. PRODUCTION AUTHORITY HASHES"

hash_file() {
    local file="$1"

    if [ ! -f "$file" ]; then
        fail "HASH_TARGET_MISSING=$file"
        return
    fi

    local hash
    hash="$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1)"

    if [ -n "$hash" ]; then
        echo "AUTHORITY_HASH=$file:$hash" | tee -a "$REPORT"
    else
        fail "HASH_FAILED=$file"
    fi
}

hash_file "app/core/config.py"
hash_file "docker-compose.yml"
hash_file "docker/nginx/Dockerfile"
hash_file "scripts/deploy.sh"
hash_file ".github/workflows/ci.yml"

section "5. PRODUCTION LEGACY TTL PROOF"

LEGACY_ACCESS="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
LEGACY_REFRESH="JWT_REFRESH_TOKEN_EXPIRES_DAYS"

PROD_LEGACY_REFS="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=node_modules \
        --exclude-dir=.next \
        --exclude-dir=dist \
        --exclude-dir=build \
        --exclude-dir=__pycache__ \
        --exclude-dir=_quarantine \
        --exclude-dir=scripts \
        "$LEGACY_ACCESS|$LEGACY_REFRESH" \
        .env.production \
        docker-compose.yml \
        docker \
        app \
        apps/web \
        2>/dev/null | wc -l
)"

echo "PRODUCTION_LEGACY_REFERENCE_COUNT=$PROD_LEGACY_REFS" | tee -a "$REPORT"

if [ "$PROD_LEGACY_REFS" -eq 0 ]; then
    pass "PRODUCTION_LEGACY_TTL_ZERO"
else
    fail "PRODUCTION_LEGACY_TTL_PRESENT"
fi

section "6. CURRENT APPLICATION RUNTIME PROOF"

RUNTIME_LEGACY_FILE_COUNT=0
RUNTIME_LEGACY_REFERENCE_COUNT=0

for root in app apps/web; do

    [ -d "$root" ] || continue

    file_count="$(
        grep -RIlE \
            --exclude-dir=.git \
            --exclude-dir=audit-output \
            --exclude-dir=node_modules \
            --exclude-dir=.next \
            --exclude-dir=dist \
            --exclude-dir=build \
            --exclude-dir=__pycache__ \
            --exclude-dir=_quarantine \
            "$LEGACY_ACCESS|$LEGACY_REFRESH" \
            "$root" 2>/dev/null | wc -l
    )"

    ref_count="$(
        grep -RInE \
            --exclude-dir=.git \
            --exclude-dir=audit-output \
            --exclude-dir=node_modules \
            --exclude-dir=.next \
            --exclude-dir=dist \
            --exclude-dir=build \
            --exclude-dir=__pycache__ \
            --exclude-dir=_quarantine \
            "$LEGACY_ACCESS|$LEGACY_REFRESH" \
            "$root" 2>/dev/null | wc -l
    )"

    RUNTIME_LEGACY_FILE_COUNT=$(
        echo $((RUNTIME_LEGACY_FILE_COUNT + file_count))
    )

    RUNTIME_LEGACY_REFERENCE_COUNT=$(
        echo $((RUNTIME_LEGACY_REFERENCE_COUNT + ref_count))
    )

done

echo "RUNTIME_LEGACY_FILE_COUNT=$RUNTIME_LEGACY_FILE_COUNT" | tee -a "$REPORT"
echo "RUNTIME_LEGACY_REFERENCE_COUNT=$RUNTIME_LEGACY_REFERENCE_COUNT" | tee -a "$REPORT"

if [ "$RUNTIME_LEGACY_FILE_COUNT" -eq 0 ] && \
   [ "$RUNTIME_LEGACY_REFERENCE_COUNT" -eq 0 ]; then
    pass "CURRENT_APPLICATION_RUNTIME_LEGACY_TTL_ZERO"
else
    fail "CURRENT_APPLICATION_RUNTIME_LEGACY_TTL_PRESENT"
fi

section "7. SECRET VALUE EXPOSURE GUARD"

SECRET_PATTERN='(DATABASE_PASSWORD|JWT_SECRET_KEY|JWT_REFRESH_SECRET_KEY|SECRET_KEY|S3_SECRET_KEY|TELEGRAM_BOT_TOKEN|API_KEY|ACCESS_KEY)'

SECRET_VALUE_LINES="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=audit-output \
        --exclude-dir=node_modules \
        --exclude-dir=.next \
        --exclude-dir=dist \
        --exclude-dir=build \
        --exclude-dir=__pycache__ \
        --exclude-dir=_quarantine \
        "$SECRET_PATTERN[[:space:]]*=" \
        .env.production \
        docker-compose.yml \
        app \
        apps/web \
        docker \
        2>/dev/null \
        | wc -l
)"

echo "SECRET_ASSIGNMENT_LINE_COUNT=$SECRET_VALUE_LINES" | tee -a "$REPORT"

if [ "$SECRET_VALUE_LINES" -eq 0 ]; then
    pass "NO_SECRET_ASSIGNMENT_LINES_DETECTED"
else
    review "SECRET_ASSIGNMENT_LINES_EXIST_BUT_VALUES_WERE_NOT_PRINTED"
fi

section "8. DEPLOYMENT MUTATION GUARD"

DEPLOY_MUTATION_SIGNALS="$(
    grep -nE \
        'docker compose (up|down|restart|pull)|docker build|docker push|kubectl (apply|delete)|git push|rm -rf|systemctl (restart|stop|start)|terraform (apply|destroy)' \
        scripts/deploy.sh \
        2>/dev/null | wc -l
)"

echo "DEPLOYMENT_MUTATION_SIGNAL_COUNT=$DEPLOY_MUTATION_SIGNALS" | tee -a "$REPORT"

if [ "$DEPLOY_MUTATION_SIGNALS" -gt 0 ]; then
    review "DEPLOY_SCRIPT_CONTAINS_MUTATION_COMMANDS_BUT_WAS_NOT_EXECUTED"
else
    pass "NO_DEPLOYMENT_MUTATION_SIGNAL_IN_DEPLOY_SCRIPT"
fi

section "9. CI PRODUCTION DEPLOYMENT GUARD"

CI_DEPLOY_SIGNALS="$(
    grep -nEi \
        'deploy|docker push|docker compose up|kubectl apply|terraform apply' \
        .github/workflows/ci.yml \
        2>/dev/null | wc -l
)"

echo "CI_DEPLOY_SIGNAL_COUNT=$CI_DEPLOY_SIGNALS" | tee -a "$REPORT"

if [ "$CI_DEPLOY_SIGNALS" -eq 0 ]; then
    pass "CI_HAS_NO_DETECTED_PRODUCTION_DEPLOYMENT_SIGNAL"
else
    review "CI_CONTAINS_DEPLOYMENT_SIGNALS_REQUIRING_BOUNDARY_AWARENESS"
fi

section "10. REMEDIATION AUTHORIZATION DECISION"

echo "CURRENT_BACKEND_AUTHORITY=app" | tee -a "$REPORT"
echo "CURRENT_FRONTEND_AUTHORITY=apps/web" | tee -a "$REPORT"
echo "CURRENT_NGINX_AUTHORITY=docker/nginx/Dockerfile" | tee -a "$REPORT"
echo "CURRENT_DEPLOY_AUTHORITY=scripts/deploy.sh" | tee -a "$REPORT"
echo "CURRENT_COMPOSE_AUTHORITY=docker-compose.yml" | tee -a "$REPORT"
echo "CURRENT_CI_AUTHORITY=.github/workflows/ci.yml" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_02_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_02_SAFETY_SIGNED_REMEDIATION_PREFLIGHT_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"

    exit 20
fi

if [ "$RUNTIME_LEGACY_FILE_COUNT" -eq 0 ] && \
   [ "$RUNTIME_LEGACY_REFERENCE_COUNT" -eq 0 ] && \
   [ "$PROD_LEGACY_REFS" -eq 0 ]; then

    if [ "$REVIEW_COUNT" -eq 0 ]; then
        echo "P0_02_STATUS=CLEAN" | tee -a "$REPORT"
        echo "RESULT=P0_02_SAFETY_SIGNED_PRODUCTION_REMEDIATION_PREFLIGHT_CLEAN" | tee -a "$REPORT"
        echo "EXIT_CODE=0" | tee -a "$REPORT"
        echo
        echo "REPORT=$REPORT"
        exit 0
    fi

    echo "P0_02_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_02_SAFETY_SIGNED_PRODUCTION_REMEDIATION_PREFLIGHT_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"
    echo
    echo "REPORT=$REPORT"
    exit 10
fi

echo "P0_02_STATUS=REVIEW" | tee -a "$REPORT"
echo "RESULT=P0_02_SAFETY_SIGNED_PRODUCTION_REMEDIATION_PREFLIGHT_REVIEW_REQUIRED" | tee -a "$REPORT"
echo "EXIT_CODE=10" | tee -a "$REPORT"
echo
echo "REPORT=$REPORT"

exit 10
