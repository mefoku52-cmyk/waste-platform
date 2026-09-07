#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="audit-output/p0_production_readiness_${STAMP}"
REPORT="$OUTPUT_DIR/P0-01-R3_authority_discriminator.txt"

mkdir -p "$OUTPUT_DIR"

FAILURE_COUNT=0
REVIEW_COUNT=0

pass() {
    echo "PASS: $*" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $*" | tee -a "$REPORT"
}

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $*" | tee -a "$REPORT"
}

section() {
    echo | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
    echo "$*" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

count_exact() {
    local pattern="$1"
    local file="$2"

    if [ ! -f "$file" ]; then
        echo "0"
        return 0
    fi

    grep -E -c "$pattern" "$file" 2>/dev/null || true
}

{
    echo "P0-01-R3 PRODUCTION AUTHORITY DISCRIMINATOR"
    echo "============================================================"
    echo "PROJECT_ROOT=$PROJECT_ROOT"
    echo "STAMP=$STAMP"
    echo "MODE=READ_ONLY"
    echo
} > "$REPORT"

section "1. SAFETY PRECHECK"

if [ "$PROJECT_ROOT" = "$HOME/waste-platform" ] || [ "$(basename "$PROJECT_ROOT")" = "waste-platform" ]; then
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
pass "BOUNDED_SCAN=YES"

section "2. CURRENT PRODUCTION SOURCE AUTHORITY"

for d in app apps/web docker alembic migrations scripts/deploy.sh .env.production; do
    if [ -e "$d" ]; then
        echo "PRESENT=$d" | tee -a "$REPORT"
    else
        echo "ABSENT=$d" | tee -a "$REPORT"
    fi
done

if [ -d app ]; then
    pass "BACKEND_SOURCE=app"
else
    fail "BACKEND_SOURCE_APP_MISSING"
fi

if [ -d apps/web ]; then
    pass "FRONTEND_SOURCE=apps/web"
else
    fail "FRONTEND_SOURCE_APPS_WEB_MISSING"
fi

section "3. DOCKERFILE AUTHORITY CLASSIFICATION"

DOCKER_BACKEND="docker/backend/Dockerfile"
DOCKER_FRONTEND="docker/frontend/Dockerfile"
DOCKER_NGINX="docker/nginx/Dockerfile"

for f in "$DOCKER_BACKEND" "$DOCKER_FRONTEND" "$DOCKER_NGINX"; do
    if [ -f "$f" ]; then
        echo "DOCKERFILE_PRESENT=$f" | tee -a "$REPORT"
    else
        echo "DOCKERFILE_ABSENT=$f" | tee -a "$REPORT"
    fi
done

if [ -f "$DOCKER_BACKEND" ]; then
    echo "--- BACKEND DOCKERFILE PATH SIGNALS ---" | tee -a "$REPORT"

    grep -nE \
        '(^|[[:space:]])(COPY|ADD)[[:space:]]+[^#]*(backend/|app/)|(^|[[:space:]])(WORKDIR|CMD|ENTRYPOINT)[[:space:]]+' \
        "$DOCKER_BACKEND" 2>/dev/null \
        | sed -E 's/(JWT_SECRET|SECRET_KEY|PASSWORD|TOKEN|DATABASE_URL|REDIS_URL)[^[:space:]]*/\1=<REDACTED>/g' \
        | tee -a "$REPORT" || true

    BACKEND_OLD="$(grep -E -c 'COPY[[:space:]]+backend/|ADD[[:space:]]+backend/' "$DOCKER_BACKEND" 2>/dev/null || true)"
    BACKEND_NEW="$(grep -E -c 'COPY[[:space:]]+app/|ADD[[:space:]]+app/' "$DOCKER_BACKEND" 2>/dev/null || true)"

    echo "BACKEND_DOCKER_OLD_PATH_SIGNALS=$BACKEND_OLD" | tee -a "$REPORT"
    echo "BACKEND_DOCKER_CURRENT_PATH_SIGNALS=$BACKEND_NEW" | tee -a "$REPORT"

    if [ "$BACKEND_OLD" -gt 0 ] && [ "$BACKEND_NEW" -eq 0 ]; then
        review "BACKEND_DOCKERFILE_REFERENCES_NONCURRENT_BACKEND_PATH"
    elif [ "$BACKEND_NEW" -gt 0 ]; then
        pass "BACKEND_DOCKERFILE_REFERENCES_CURRENT_APP_PATH"
    else
        review "BACKEND_DOCKERFILE_SOURCE_COPY_PATH_NOT_RESOLVED"
    fi
fi

if [ -f "$DOCKER_FRONTEND" ]; then
    echo "--- FRONTEND DOCKERFILE PATH SIGNALS ---" | tee -a "$REPORT"

    grep -nE \
        '(^|[[:space:]])(COPY|ADD)[[:space:]]+[^#]*(frontend/|apps/web/)|(^|[[:space:]])(WORKDIR|CMD|ENTRYPOINT)[[:space:]]+' \
        "$DOCKER_FRONTEND" 2>/dev/null \
        | sed -E 's/(JWT_SECRET|SECRET_KEY|PASSWORD|TOKEN|DATABASE_URL|REDIS_URL)[^[:space:]]*/\1=<REDACTED>/g' \
        | tee -a "$REPORT" || true

    FRONTEND_OLD="$(grep -E -c 'COPY[[:space:]]+frontend/|ADD[[:space:]]+frontend/' "$DOCKER_FRONTEND" 2>/dev/null || true)"
    FRONTEND_NEW="$(grep -E -c 'COPY[[:space:]]+apps/web/|ADD[[:space:]]+apps/web/' "$DOCKER_FRONTEND" 2>/dev/null || true)"

    echo "FRONTEND_DOCKER_OLD_PATH_SIGNALS=$FRONTEND_OLD" | tee -a "$REPORT"
    echo "FRONTEND_DOCKER_CURRENT_PATH_SIGNALS=$FRONTEND_NEW" | tee -a "$REPORT"

    if [ "$FRONTEND_OLD" -gt 0 ] && [ "$FRONTEND_NEW" -eq 0 ]; then
        review "FRONTEND_DOCKERFILE_REFERENCES_NONCURRENT_FRONTEND_PATH"
    elif [ "$FRONTEND_NEW" -gt 0 ]; then
        pass "FRONTEND_DOCKERFILE_REFERENCES_CURRENT_APPS_WEB_PATH"
    else
        review "FRONTEND_DOCKERFILE_SOURCE_COPY_PATH_NOT_RESOLVED"
    fi
fi

section "4. ROOT DOCKERFILE / WORKER AUTHORITY"

for f in Dockerfile worker/Dockerfile docker/backend/Dockerfile docker/frontend/Dockerfile docker/nginx/Dockerfile; do
    if [ -f "$f" ]; then
        echo "DOCKER_ARTIFACT=$f" | tee -a "$REPORT"

        grep -nE \
            '(^FROM[[:space:]]|^[[:space:]]*(COPY|ADD)[[:space:]]|^[[:space:]]*(CMD|ENTRYPOINT)[[:space:]])' \
            "$f" 2>/dev/null \
            | head -80 \
            | tee -a "$REPORT" || true
    fi
done

section "5. COMPOSE AUTHORITY INVENTORY"

COMPOSE_FOUND=0

for f in \
    docker-compose.production.yml \
    docker-compose.production.yaml \
    compose.production.yml \
    compose.production.yaml \
    docker-compose.yml \
    docker-compose.yaml \
    compose.yml \
    compose.yaml \
    docker/compose.production.yml \
    docker/docker-compose.production.yml
do
    if [ -f "$f" ]; then
        COMPOSE_FOUND=$((COMPOSE_FOUND + 1))
        echo "COMPOSE_CANDIDATE=$f" | tee -a "$REPORT"
    fi
done

echo "COMPOSE_CANDIDATE_COUNT=$COMPOSE_FOUND" | tee -a "$REPORT"

if [ "$COMPOSE_FOUND" -eq 0 ]; then
    review "NO_COMPOSE_PRODUCTION_AUTHORITY_FOUND"
else
    pass "COMPOSE_CANDIDATES_EXIST=$COMPOSE_FOUND"
fi

section "6. COMPOSE PRODUCTION SIGNAL CLASSIFICATION"

for f in \
    docker-compose.production.yml \
    docker-compose.production.yaml \
    compose.production.yml \
    compose.production.yaml \
    docker-compose.yml \
    docker-compose.yaml \
    compose.yml \
    compose.yaml \
    docker/compose.production.yml \
    docker/docker-compose.production.yml
do
    if [ -f "$f" ]; then
        echo "--- $f ---" | tee -a "$REPORT"

        grep -nE \
            '(^|[[:space:]])(services:|backend:|frontend:|nginx:|postgres:|postgresql:|redis:|worker:|api:)|image:|build:|env_file:|environment:|ports:|volumes:|networks:' \
            "$f" 2>/dev/null \
            | sed -E 's/(JWT_SECRET|SECRET_KEY|PASSWORD|TOKEN|DATABASE_URL|REDIS_URL|API_KEY)[[:space:]]*[:=][^[:space:]]*/\1=<REDACTED>/g' \
            | head -160 \
            | tee -a "$REPORT" || true
    fi
done

section "7. DEPLOY SCRIPT AUTHORITY"

DEPLOY="scripts/deploy.sh"

if [ -f "$DEPLOY" ]; then
    pass "DEPLOY_SCRIPT_PRESENT=$DEPLOY"

    echo "--- DEPLOY PATH SIGNALS ---" | tee -a "$REPORT"

    grep -nE \
        'docker|compose|Dockerfile|backend/|frontend/|app/|apps/web/|production|\.env' \
        "$DEPLOY" 2>/dev/null \
        | sed -E 's/(JWT_SECRET|SECRET_KEY|PASSWORD|TOKEN|DATABASE_URL|REDIS_URL|API_KEY)[^[:space:]]*/\1=<REDACTED>/g' \
        | head -200 \
        | tee -a "$REPORT" || true
else
    fail "DEPLOY_SCRIPT_MISSING=$DEPLOY"
fi

section "8. CI AUTHORITY CLASSIFICATION"

CI=".github/workflows/ci.yml"

if [ -f "$CI" ]; then
    pass "CI_PRESENT=$CI"

    echo "--- CI DOCKER SIGNALS ---" | tee -a "$REPORT"

    grep -nE \
        'docker build|docker compose|dockerfile:|Dockerfile|deploy|production|push|publish|release' \
        "$CI" 2>/dev/null \
        | sed -E 's/(JWT_SECRET|SECRET_KEY|PASSWORD|TOKEN|DATABASE_URL|REDIS_URL|API_KEY)[^[:space:]]*/\1=<REDACTED>/g' \
        | head -160 \
        | tee -a "$REPORT" || true

    CI_DEPLOY="$(grep -Ei -c 'deploy|production|push|publish|release' "$CI" 2>/dev/null || true)"
    CI_BUILD="$(grep -Ei -c 'docker build|dockerfile:' "$CI" 2>/dev/null || true)"
    CI_TEST="$(grep -Ei -c 'pytest|vitest|npm run test|npm run typecheck|npm run lint' "$CI" 2>/dev/null || true)"

    echo "CI_DEPLOY_SIGNALS=$CI_DEPLOY" | tee -a "$REPORT"
    echo "CI_DOCKER_BUILD_SIGNALS=$CI_BUILD" | tee -a "$REPORT"
    echo "CI_TEST_SIGNALS=$CI_TEST" | tee -a "$REPORT"
else
    fail "CI_FILE_MISSING=$CI"
fi

section "9. ACTIVE VS FORENSIC LEGACY TTL DISCRIMINATION"

LEGACY_A="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
LEGACY_R="JWT_REFRESH_TOKEN_EXPIRES_DAYS"

echo "LEGACY_ACCESS=$LEGACY_A" | tee -a "$REPORT"
echo "LEGACY_REFRESH=$LEGACY_R" | tee -a "$REPORT"

ACTIVE_FILES=0
ACTIVE_REFS=0
HISTORICAL_FILES=0
HISTORICAL_REFS=0

while IFS= read -r -d '' f; do

    case "$f" in
        ./scripts/forensics/archive/*)
            HISTORICAL_FILES=$((HISTORICAL_FILES + 1))

            A="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"
            HISTORICAL_REFS=$((HISTORICAL_REFS + A))
            ;;

        ./audit-output/*)
            ;;

        ./_quarantine/*)
            HISTORICAL_FILES=$((HISTORICAL_FILES + 1))
            A="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"
            HISTORICAL_REFS=$((HISTORICAL_REFS + A))
            ;;

        *.bak-*|*.backup-*|*.before-*|*.orig)
            HISTORICAL_FILES=$((HISTORICAL_FILES + 1))
            A="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"
            HISTORICAL_REFS=$((HISTORICAL_REFS + A))
            ;;

        *)
            A="$(grep -E -c "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null || true)"

            if [ "$A" -gt 0 ]; then
                ACTIVE_FILES=$((ACTIVE_FILES + 1))
                ACTIVE_REFS=$((ACTIVE_REFS + A))

                echo "ACTIVE_LEGACY_FILE=$f" | tee -a "$REPORT"

                grep -nE "$LEGACY_A|$LEGACY_R" "$f" 2>/dev/null \
                    | head -40 \
                    | tee -a "$REPORT" || true
            fi
            ;;
    esac

done < <(
    find . \
        -type f \
        \( -name '*.py' -o -name '*.sh' -o -name '*.yml' -o -name '*.yaml' -o -name '*.toml' -o -name '*.ini' -o -name '*.conf' -o -name '*.md' \) \
        -not -path './.git/*' \
        -not -path './apps/web/node_modules/*' \
        -not -path './apps/web/.next/*' \
        -not -path './.venv/*' \
        -print0 2>/dev/null
)

echo "ACTIVE_LEGACY_FILE_COUNT=$ACTIVE_FILES" | tee -a "$REPORT"
echo "ACTIVE_LEGACY_REFERENCE_TOTAL=$ACTIVE_REFS" | tee -a "$REPORT"
echo "HISTORICAL_LEGACY_FILE_COUNT=$HISTORICAL_FILES" | tee -a "$REPORT"
echo "HISTORICAL_LEGACY_REFERENCE_TOTAL=$HISTORICAL_REFS" | tee -a "$REPORT"

if [ "$ACTIVE_REFS" -eq 0 ]; then
    pass "ACTIVE_RUNTIME_LEGACY_TTL=0"
else
    review "ACTIVE_RUNTIME_LEGACY_TTL=$ACTIVE_REFS"
fi

section "10. CURRENT RUNTIME HASH CONTINUITY"

for f in \
    app/core/config.py \
    app/shared/infrastructure/security/jwt_service.py
do
    if [ -f "$f" ]; then
        echo "RUNTIME_HASH=$(sha256sum "$f" | awk '{print $1}')  $f" | tee -a "$REPORT"
    else
        fail "RUNTIME_FILE_MISSING=$f"
    fi
done

EXPECTED_CONFIG="742d629996182344fc2ce2bc8c5253eaef185c47856cdede2f91a486a0b1256d"
EXPECTED_JWT="eceaf6010b755ca0ff191be5ab2e9ef0b777304b94df754d878cb6bafc6ce57c"

ACTUAL_CONFIG="$(sha256sum app/core/config.py 2>/dev/null | awk '{print $1}')"
ACTUAL_JWT="$(sha256sum app/shared/infrastructure/security/jwt_service.py 2>/dev/null | awk '{print $1}')"

if [ "$ACTUAL_CONFIG" = "$EXPECTED_CONFIG" ]; then
    pass "CONFIG_HASH_IMMUTABLE_MATCH"
else
    fail "CONFIG_HASH_MISMATCH expected=$EXPECTED_CONFIG actual=$ACTUAL_CONFIG"
fi

if [ "$ACTUAL_JWT" = "$EXPECTED_JWT" ]; then
    pass "JWT_SERVICE_HASH_IMMUTABLE_MATCH"
else
    fail "JWT_SERVICE_HASH_MISMATCH expected=$EXPECTED_JWT actual=$ACTUAL_JWT"
fi

section "11. DATABASE AUTHORITY SNAPSHOT"

if [ -f alembic.ini ]; then
    echo "ALEMBIC_INI_PRESENT=YES" | tee -a "$REPORT"

    grep -nE \
        'script_location|sqlalchemy.url|prepend_sys_path|version_path_separator' \
        alembic.ini 2>/dev/null \
        | sed -E 's#(sqlalchemy.url[[:space:]]*=[[:space:]]*).*$#\1<REDACTED>#' \
        | tee -a "$REPORT" || true
else
    review "ALEMBIC_INI_MISSING"
fi

if [ -f app/shared/infrastructure/db/session.py ]; then
    echo "--- DB SESSION AUTHORITY ---" | tee -a "$REPORT"

    grep -nE \
        'DATABASE_URL|ASYNC_DATABASE_URL|SYNC_DATABASE_URL|sqlite|asyncpg|create_async_engine|create_engine' \
        app/shared/infrastructure/db/session.py 2>/dev/null \
        | sed -E 's#(DATABASE_URL[[:space:]]*=[[:space:]]*).*$#\1<REDACTED>#' \
        | tee -a "$REPORT" || true
fi

if [ -f app/core/config.py ]; then
    echo "--- CONFIG DATABASE AUTHORITY ---" | tee -a "$REPORT"

    grep -nE \
        'DATABASE_URL|SQLITE_DEFAULT|development|production|postgres|asyncpg' \
        app/core/config.py 2>/dev/null \
        | sed -E 's#(DATABASE_URL[^=]*=[[:space:]]*).*$#\1<REDACTED>#' \
        | tee -a "$REPORT" || true
fi

section "12. AUTHORITY DECISION"

echo "PRODUCTION_BACKEND_AUTHORITY=app" | tee -a "$REPORT"
echo "PRODUCTION_FRONTEND_AUTHORITY=apps/web" | tee -a "$REPORT"
echo "PRODUCTION_NGINX_AUTHORITY=docker/nginx/Dockerfile" | tee -a "$REPORT"
echo "PRODUCTION_DEPLOY_AUTHORITY=scripts/deploy.sh" | tee -a "$REPORT"
echo "CI_AUTHORITY=.github/workflows/ci.yml" | tee -a "$REPORT"

if [ "$COMPOSE_FOUND" -eq 1 ]; then
    echo "PRODUCTION_COMPOSE_AUTHORITY=UNIQUE_CANDIDATE" | tee -a "$REPORT"
elif [ "$COMPOSE_FOUND" -eq 0 ]; then
    echo "PRODUCTION_COMPOSE_AUTHORITY=UNRESOLVED" | tee -a "$REPORT"
else
    echo "PRODUCTION_COMPOSE_AUTHORITY=AMBIGUOUS_${COMPOSE_FOUND}_CANDIDATES" | tee -a "$REPORT"
    review "MULTIPLE_COMPOSE_CANDIDATES"
fi

if [ "$ACTIVE_REFS" -eq 0 ]; then
    pass "LEGACY_RUNTIME_AUTHORITY=NONE"
else
    review "LEGACY_RUNTIME_AUTHORITY_REQUIRES_TARGETED_REVIEW"
fi

section "13. FINAL CLASSIFICATION"

echo "ACTIVE_LEGACY_FILES=$ACTIVE_FILES" | tee -a "$REPORT"
echo "ACTIVE_LEGACY_REFS=$ACTIVE_REFS" | tee -a "$REPORT"
echo "HISTORICAL_LEGACY_FILES=$HISTORICAL_FILES" | tee -a "$REPORT"
echo "HISTORICAL_LEGACY_REFS=$HISTORICAL_REFS" | tee -a "$REPORT"
echo "COMPOSE_CANDIDATES=$COMPOSE_FOUND" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -eq 0 ] && \
   [ "$ACTIVE_REFS" -eq 0 ] && \
   [ "$COMPOSE_FOUND" -eq 1 ]; then

    pass "P0_01_R3_AUTHORITY_BOUNDARY_CLEAN"
    echo "P0_01_R3_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R3_PRODUCTION_AUTHORITY_BOUNDARY_CLEAN" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 0

elif [ "$FAILURE_COUNT" -gt 0 ]; then

    echo "P0_01_R3_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R3_PRODUCTION_AUTHORITY_FAILURE" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 20

else

    echo "P0_01_R3_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_01_R3_PRODUCTION_AUTHORITY_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"

    echo
    echo "REPORT=$REPORT"
    exit 10
fi
