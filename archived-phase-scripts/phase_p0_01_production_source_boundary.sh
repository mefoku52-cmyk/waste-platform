#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="$PROJECT_ROOT/audit-output/p0_production_readiness_$STAMP"
REPORT="$OUTPUT_DIR/P0-01_production_source_boundary.txt"

mkdir -p "$OUTPUT_DIR"

FAILURE_COUNT=0
REVIEW_COUNT=0

fail() {
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "FAIL: $*" | tee -a "$REPORT"
}

review() {
    REVIEW_COUNT=$((REVIEW_COUNT + 1))
    echo "REVIEW: $*" | tee -a "$REPORT"
}

pass() {
    echo "PASS: $*" | tee -a "$REPORT"
}

section() {
    echo
    echo "============================================================" | tee -a "$REPORT"
    echo "$*" | tee -a "$REPORT"
    echo "============================================================" | tee -a "$REPORT"
}

run_bounded() {
    local label="$1"
    shift

    echo
    echo "--- $label ---" | tee -a "$REPORT"

    if "$@" >>"$REPORT" 2>&1; then
        :
    else
        review "$label command returned non-zero"
    fi
}

echo "============================================================" | tee "$REPORT"
echo " P0-01 PRODUCTION SOURCE BOUNDARY"
echo "============================================================" | tee -a "$REPORT"
echo "PROJECT_ROOT=$PROJECT_ROOT" | tee -a "$REPORT"
echo "STAMP=$STAMP" | tee -a "$REPORT"
echo "MODE=READ_ONLY" | tee -a "$REPORT"
echo "SOURCE_WRITES=0" | tee -a "$REPORT"
echo "RUNTIME_EXECUTION=0" | tee -a "$REPORT"
echo "BUILD=0" | tee -a "$REPORT"
echo "DEPLOYMENT=0" | tee -a "$REPORT"
echo "DELETIONS=0" | tee -a "$REPORT"

cd "$PROJECT_ROOT" || exit 2

section "1. PROJECT IDENTITY"

printf 'PWD=' | tee -a "$REPORT"
pwd | tee -a "$REPORT"

printf 'GIT_ROOT=' | tee -a "$REPORT"
git rev-parse --show-toplevel 2>/dev/null | tee -a "$REPORT" || true

printf 'GIT_BRANCH=' | tee -a "$REPORT"
git branch --show-current 2>/dev/null | tee -a "$REPORT" || true

printf 'GIT_HEAD=' | tee -a "$REPORT"
git rev-parse HEAD 2>/dev/null | tee -a "$REPORT" || true

section "2. TOP-LEVEL PRODUCTION CANDIDATES"

for path in \
    app \
    apps \
    docker \
    alembic \
    migrations \
    scripts \
    tests \
    docs \
    README.md \
    Dockerfile \
    docker-compose.yml \
    docker-compose.production.yml \
    docker-compose.production.yaml \
    .env \
    .env.production \
    .env.example \
    pyproject.toml \
    requirements.txt \
    requirements-prod.txt \
    package.json \
    pnpm-lock.yaml \
    package-lock.json \
    yarn.lock \
    Makefile
do
    if [ -e "$path" ]; then
        pass "EXISTS $path"
        ls -ld "$path" 2>/dev/null | tee -a "$REPORT"
    else
        echo "ABSENT $path" | tee -a "$REPORT"
    fi
done

section "3. BACKEND PRODUCTION TREE"

if [ -d app ]; then
    find app \
        -type f \
        -not -path '*/__pycache__/*' \
        -not -path '*/.pytest_cache/*' \
        -not -path '*/.mypy_cache/*' \
        -not -path '*/.ruff_cache/*' \
        | sort | head -n 500 | tee -a "$REPORT"

    APP_COUNT="$(find app -type f \
        -not -path '*/__pycache__/*' \
        -not -path '*/.pytest_cache/*' \
        -not -path '*/.mypy_cache/*' \
        -not -path '*/.ruff_cache/*' \
        | wc -l)"

    echo "APP_SOURCE_FILE_COUNT=$APP_COUNT" | tee -a "$REPORT"

    if [ "$APP_COUNT" -gt 0 ]; then
        pass "Backend source tree exists"
    else
        fail "Backend app/ contains no source files"
    fi
else
    fail "Missing backend app/ directory"
fi

section "4. FRONTEND PRODUCTION TREE"

if [ -d apps/web ]; then
    find apps/web \
        -type f \
        -not -path '*/node_modules/*' \
        -not -path '*/.next/*' \
        -not -path '*/dist/*' \
        -not -path '*/build/*' \
        | sort | head -n 500 | tee -a "$REPORT"

    WEB_COUNT="$(find apps/web \
        -type f \
        -not -path '*/node_modules/*' \
        -not -path '*/.next/*' \
        -not -path '*/dist/*' \
        -not -path '*/build/*' \
        | wc -l)"

    echo "FRONTEND_SOURCE_FILE_COUNT=$WEB_COUNT" | tee -a "$REPORT"

    if [ "$WEB_COUNT" -gt 0 ]; then
        pass "Frontend source tree exists"
    else
        fail "Frontend source tree is empty"
    fi
else
    fail "Missing apps/web frontend"
fi

section "5. PRODUCTION DOCKER ARTIFACTS"

for path in \
    docker/backend/Dockerfile \
    docker/frontend/Dockerfile \
    docker/nginx/Dockerfile \
    docker/nginx/conf.d/cmep.conf \
    docker-compose.production.yml
do
    if [ -f "$path" ]; then
        pass "Production artifact present: $path"
    else
        review "Production artifact missing: $path"
    fi
done

section "6. COMPOSE INVENTORY"

find . \
    -maxdepth 3 \
    -type f \
    \( \
        -name 'docker-compose*.yml' \
        -o -name 'docker-compose*.yaml' \
    \) \
    -not -path './node_modules/*' \
    -not -path './audit-output/*' \
    | sort | tee -a "$REPORT"

COMPOSE_COUNT="$(
    find . \
        -maxdepth 3 \
        -type f \
        \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' \) \
        -not -path './node_modules/*' \
        -not -path './audit-output/*' \
        | wc -l
)"

echo "COMPOSE_FILE_COUNT=$COMPOSE_COUNT" | tee -a "$REPORT"

if [ "$COMPOSE_COUNT" -gt 0 ]; then
    pass "Compose definitions discovered"
else
    fail "No compose definitions discovered"
fi

section "7. DEPLOYMENT SCRIPT INVENTORY"

for path in \
    scripts/deploy.sh \
    scripts/backup.sh \
    scripts/restore.sh \
    scripts/health-check.sh \
    scripts/bootstrap-letsencrypt.sh
do
    if [ -f "$path" ]; then
        pass "Script present: $path"
        sha256sum "$path" | tee -a "$REPORT"
    else
        review "Expected operational script absent: $path"
    fi
done

section "8. ENVIRONMENT FILE INVENTORY"

find . \
    -maxdepth 3 \
    -type f \
    \( \
        -name '.env' \
        -o -name '.env.*' \
    \) \
    -not -path './node_modules/*' \
    -not -path './audit-output/*' \
    | sort | tee -a "$REPORT"

ENV_COUNT="$(
    find . \
        -maxdepth 3 \
        -type f \
        \( -name '.env' -o -name '.env.*' \) \
        -not -path './node_modules/*' \
        -not -path './audit-output/*' \
        | wc -l
)"

echo "ENV_FILE_COUNT=$ENV_COUNT" | tee -a "$REPORT"

if [ -f .env.production ]; then
    pass ".env.production exists"
else
    review ".env.production not found"
fi

if [ -f .env.example ]; then
    pass ".env.example exists"
else
    review ".env.example not found"
fi

section "9. PRODUCTION ENVIRONMENT KEY CLASSIFICATION"

for envfile in \
    .env.production \
    .env.example \
    .env.compose \
    .env
do
    if [ -f "$envfile" ]; then
        echo | tee -a "$REPORT"
        echo "### $envfile" | tee -a "$REPORT"

        grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$envfile" \
            2>/dev/null \
            | sed -E 's/=.*$/=<REDACTED>/' \
            | sort \
            | tee -a "$REPORT"
    fi
done

section "10. LEGACY TTL AUTHORITY RECHECK"

LEGACY_ACCESS='JWT_ACCESS_TOKEN_EXPIRES_MINUTES'
LEGACY_REFRESH='JWT_REFRESH_TOKEN_EXPIRES_DAYS'

for target in \
    app \
    apps/web \
    docker \
    scripts \
    alembic \
    migrations \
    docs \
    README.md \
    pyproject.toml \
    package.json
do
    if [ -e "$target" ]; then
        MATCHES="$(
            grep -RInE \
                "$LEGACY_ACCESS|$LEGACY_REFRESH" \
                "$target" \
                --exclude-dir=node_modules \
                --exclude-dir=.next \
                --exclude-dir=.venv \
                --exclude-dir=__pycache__ \
                --exclude-dir=.git \
                2>/dev/null || true
        )"

        if [ -n "$MATCHES" ]; then
            echo "$MATCHES" | tee -a "$REPORT"
            review "Legacy TTL reference found in production-relevant candidate: $target"
        fi
    fi
done

section "11. CANONICAL TTL AUTHORITY"

for target in \
    app \
    apps/web \
    docker \
    scripts \
    alembic \
    migrations \
    docs \
    README.md
do
    if [ -e "$target" ]; then
        grep -RInE \
            'ACCESS_TOKEN_EXPIRE_MINUTES|REFRESH_TOKEN_EXPIRE_DAYS' \
            "$target" \
            --exclude-dir=node_modules \
            --exclude-dir=.next \
            --exclude-dir=.venv \
            --exclude-dir=__pycache__ \
            --exclude-dir=.git \
            2>/dev/null \
            | head -n 200 \
            | tee -a "$REPORT" || true
    fi
done

section "12. BACKEND ENTRYPOINT CANDIDATES"

find app . \
    -maxdepth 5 \
    -type f \
    \( \
        -name 'main.py' \
        -o -name 'app.py' \
        -o -name 'server.py' \
        -o -name 'asgi.py' \
        -o -name 'wsgi.py' \
        -o -name 'entrypoint.sh' \
        -o -name 'start.sh' \
    \) \
    -not -path './node_modules/*' \
    -not -path './.venv/*' \
    -not -path './audit-output/*' \
    -not -path './.git/*' \
    | sort \
    | tee -a "$REPORT"

section "13. FRONTEND PACKAGE DEFINITIONS"

for path in \
    package.json \
    apps/web/package.json
do
    if [ -f "$path" ]; then
        echo "### $path" | tee -a "$REPORT"

        if command -v jq >/dev/null 2>&1; then
            jq '{
                name,
                version,
                private,
                scripts,
                engines
            }' "$path" 2>/dev/null | tee -a "$REPORT" || true
        else
            sed -n '1,220p' "$path" | tee -a "$REPORT"
        fi
    fi
done

section "14. BACKEND PACKAGE DEFINITIONS"

for path in \
    pyproject.toml \
    requirements.txt \
    requirements-prod.txt
do
    if [ -f "$path" ]; then
        echo "### $path" | tee -a "$REPORT"
        sed -n '1,260p' "$path" | tee -a "$REPORT"
    fi
done

section "15. MIGRATION SURFACE"

for path in \
    alembic.ini \
    alembic \
    migrations
do
    if [ -e "$path" ]; then
        echo "### $path" | tee -a "$REPORT"

        if [ -d "$path" ]; then
            find "$path" \
                -type f \
                | sort \
                | head -n 500 \
                | tee -a "$REPORT"
        else
            sed -n '1,260p' "$path" | tee -a "$REPORT"
        fi
    fi
done

section "16. DATABASE CONFIGURATION REFERENCES"

grep -RInE \
    'DATABASE_URL|POSTGRES|postgresql|redis|REDIS_URL' \
    app \
    docker \
    docker-compose.production.yml \
    2>/dev/null \
    | sed -E \
        's/(password=)[^[:space:];]+/\1<REDACTED>/Ig;
         s/(://)[^@[:space:]]+@/\1<REDACTED>@/g' \
    | head -n 400 \
    | tee -a "$REPORT" || true

section "17. TEST SURFACE"

for path in \
    tests \
    app/tests \
    test
do
    if [ -d "$path" ]; then
        COUNT="$(
            find "$path" \
                -type f \
                \( -name 'test_*.py' -o -name '*_test.py' -o -name '*.test.ts' -o -name '*.test.tsx' \) \
                | wc -l
        )"

        echo "$path TEST_FILE_COUNT=$COUNT" | tee -a "$REPORT"

        if [ "$COUNT" -gt 0 ]; then
            pass "Tests discovered under $path"
        else
            review "Test directory exists but no recognized test files found: $path"
        fi
    fi
done

section "18. CI/CD SURFACE"

find .github \
    -maxdepth 4 \
    -type f \
    2>/dev/null \
    | sort \
    | tee -a "$REPORT"

if [ -d .github/workflows ]; then
    for workflow in .github/workflows/*; do
        [ -f "$workflow" ] || continue

        echo | tee -a "$REPORT"
        echo "### WORKFLOW $workflow" | tee -a "$REPORT"

        grep -nE \
            'deploy|production|docker|build|test|pytest|npm|pnpm|yarn|migration|alembic' \
            "$workflow" \
            2>/dev/null \
            | head -n 300 \
            | tee -a "$REPORT" || true
    done
fi

section "19. PRODUCTION DOCKERFILE STATIC SIGNALS"

for dockerfile in \
    docker/backend/Dockerfile \
    docker/frontend/Dockerfile \
    docker/nginx/Dockerfile
do
    if [ -f "$dockerfile" ]; then
        echo | tee -a "$REPORT"
        echo "### $dockerfile" | tee -a "$REPORT"

        grep -nE \
            'FROM|WORKDIR|COPY|RUN|CMD|ENTRYPOINT|EXPOSE|HEALTHCHECK|ENV|USER' \
            "$dockerfile" \
            2>/dev/null \
            | head -n 300 \
            | tee -a "$REPORT"
    fi
done

section "20. PRODUCTION COMPOSE STATIC SIGNALS"

if [ -f docker-compose.production.yml ]; then
    grep -nE \
        'services:|image:|build:|ports:|expose:|environment:|env_file:|depends_on:|healthcheck:|volumes:|networks:|restart:|command:' \
        docker-compose.production.yml \
        2>/dev/null \
        | head -n 500 \
        | tee -a "$REPORT"
else
    review "docker-compose.production.yml absent"
fi

section "21. OBSERVABILITY SURFACE"

for path in \
    prometheus \
    grafana \
    loki \
    promtail \
    alertmanager \
    monitoring
do
    if [ -e "$path" ]; then
        pass "Observability surface present: $path"
    fi
done

find . \
    -maxdepth 4 \
    -type f \
    \( \
        -iname '*prometheus*' \
        -o -iname '*grafana*' \
        -iname '*alertmanager*' \
        -o -iname '*loki*' \
        -o -iname '*promtail*' \
    \) \
    -not -path './node_modules/*' \
    -not -path './.venv/*' \
    -not -path './audit-output/*' \
    | sort \
    | head -n 300 \
    | tee -a "$REPORT"

section "22. BACKUP / RESTORE SURFACE"

for path in \
    scripts/backup.sh \
    scripts/restore.sh \
    scripts/backup/backup-db.sh
do
    if [ -f "$path" ]; then
        pass "Backup/restore script present: $path"
    else
        review "Backup/restore artifact absent: $path"
    fi
done

section "23. SOURCE-CONTROL STATUS"

git status --short 2>/dev/null | head -n 500 | tee -a "$REPORT" || true

section "24. LARGE GENERATED / NON-PRODUCTION SURFACES"

for path in \
    node_modules \
    apps/web/node_modules \
    apps/web/.next \
    .venv \
    venv \
    audit-output \
    dist \
    build
do
    if [ -e "$path" ]; then
        echo "PRESENT_NON_PRODUCTION_CANDIDATE=$path" | tee -a "$REPORT"
    fi
done

section "25. PRODUCTION SOURCE BOUNDARY CLASSIFICATION"

echo "The following are candidate production authorities:" | tee -a "$REPORT"

for path in \
    app \
    apps/web \
    docker \
    docker-compose.production.yml \
    scripts/deploy.sh \
    alembic \
    migrations \
    .env.production
do
    if [ -e "$path" ]; then
        echo "CANDIDATE_PRODUCTION_AUTHORITY=$path" | tee -a "$REPORT"
    fi
done

echo | tee -a "$REPORT"
echo "The following are explicitly classified as non-authoritative unless later evidence proves otherwise:" | tee -a "$REPORT"

for path in \
    audit-output \
    node_modules \
    apps/web/node_modules \
    apps/web/.next \
    .venv \
    venv \
    dist \
    build
do
    if [ -e "$path" ]; then
        echo "NON_AUTHORITATIVE_CANDIDATE=$path" | tee -a "$REPORT"
    fi
done

section "26. SAFETY ATTESTATION"

echo "READ_ONLY=YES" | tee -a "$REPORT"
echo "NO_SOURCE_WRITES=YES" | tee -a "$REPORT"
echo "NO_RUNTIME_EXECUTION=YES" | tee -a "$REPORT"
echo "NO_ENV_EXECUTION=YES" | tee -a "$REPORT"
echo "NO_BUILD=YES" | tee -a "$REPORT"
echo "NO_DEPLOYMENT=YES" | tee -a "$REPORT"
echo "NO_DELETIONS=YES" | tee -a "$REPORT"
echo "BOUNDED_SCAN=YES" | tee -a "$REPORT"

section "27. FINAL"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -eq 0 ] && [ "$REVIEW_COUNT" -eq 0 ]; then
    echo "P0_01_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_PRODUCTION_SOURCE_BOUNDARY_COMPLETE" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"
    exit 0
elif [ "$FAILURE_COUNT" -eq 0 ]; then
    echo "P0_01_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_01_PRODUCTION_SOURCE_BOUNDARY_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"
    exit 10
else
    echo "P0_01_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_PRODUCTION_SOURCE_BOUNDARY_FAILED" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    exit 20
fi
