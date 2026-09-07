#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="$PROJECT_ROOT/audit-output/p0_production_readiness_$STAMP"
REPORT="$OUTPUT_DIR/P0-01-R2_production_authority_resolver.txt"

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

show_file() {
    local file="$1"
    local max_lines="${2:-260}"

    if [ -f "$file" ]; then
        echo | tee -a "$REPORT"
        echo "### FILE=$file" | tee -a "$REPORT"
        sed -n "1,${max_lines}p" "$file" | tee -a "$REPORT"
    fi
}

grep_file() {
    local file="$1"
    local pattern="$2"

    if [ -f "$file" ]; then
        echo | tee -a "$REPORT"
        echo "### MATCHES=$file" | tee -a "$REPORT"
        grep -nE "$pattern" "$file" 2>/dev/null \
            | head -n 300 \
            | tee -a "$REPORT" || true
    fi
}

echo "============================================================" | tee "$REPORT"
echo " P0-01-R2 PRODUCTION AUTHORITY RESOLVER" | tee -a "$REPORT"
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

section "1. GIT IDENTITY"

echo "GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)" | tee -a "$REPORT"
echo "GIT_BRANCH=$(git branch --show-current 2>/dev/null || true)" | tee -a "$REPORT"
echo "GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || true)" | tee -a "$REPORT"

section "2. BACKEND PATH AUTHORITY"

echo "Expected current backend source:"
echo "app/" | tee -a "$REPORT"

if [ -d app ]; then
    pass "app/ exists"
else
    fail "app/ missing"
fi

if [ -f app/main.py ]; then
    pass "app/main.py exists"
    sha256sum app/main.py | tee -a "$REPORT"
else
    fail "app/main.py missing"
fi

echo | tee -a "$REPORT"
echo "Backend candidates outside quarantine/archive:" | tee -a "$REPORT"

find . \
    -type f \
    \( -name 'main.py' -o -name 'app.py' -o -name 'server.py' \) \
    -not -path './.git/*' \
    -not -path './_quarantine/*' \
    -not -path './archive/*' \
    -not -path './audit-output/*' \
    -not -path './node_modules/*' \
    -not -path './.venv/*' \
    | sort \
    | tee -a "$REPORT"

section "3. BACKEND DOCKERFILE AUTHORITY"

for file in \
    Dockerfile \
    docker/backend/Dockerfile \
    backend/Dockerfile \
    app/Dockerfile
do
    if [ -f "$file" ]; then
        echo "PRESENT_DOCKERFILE=$file" | tee -a "$REPORT"
        sha256sum "$file" | tee -a "$REPORT"

        grep_file "$file" \
            '^(FROM|WORKDIR|COPY|ADD|RUN|USER|ENV|EXPOSE|HEALTHCHECK|CMD|ENTRYPOINT)'
    fi
done

section "4. BACKEND DOCKER PATH CONSISTENCY"

for file in \
    docker/backend/Dockerfile \
    Dockerfile
do
    if [ -f "$file" ]; then
        echo | tee -a "$REPORT"
        echo "### PATH REFERENCES IN $file" | tee -a "$REPORT"

        grep -nE \
            '(^|[[:space:]])(app|backend|frontend|apps/web)(/|[[:space:]]|$)' \
            "$file" \
            2>/dev/null \
            | head -n 200 \
            | tee -a "$REPORT" || true
    fi
done

section "5. FRONTEND PATH AUTHORITY"

if [ -d apps/web ]; then
    pass "apps/web exists"
else
    fail "apps/web missing"
fi

if [ -f apps/web/package.json ]; then
    pass "apps/web/package.json exists"
else
    fail "apps/web/package.json missing"
fi

echo | tee -a "$REPORT"
echo "Frontend candidates:" | tee -a "$REPORT"

find . \
    -maxdepth 4 \
    -type f \
    -name package.json \
    -not -path './node_modules/*' \
    -not -path './apps/web/node_modules/*' \
    -not -path './audit-output/*' \
    | sort \
    | tee -a "$REPORT"

section "6. FRONTEND DOCKERFILE AUTHORITY"

for file in \
    docker/frontend/Dockerfile \
    frontend/Dockerfile \
    apps/web/Dockerfile
do
    if [ -f "$file" ]; then
        echo "PRESENT_FRONTEND_DOCKERFILE=$file" | tee -a "$REPORT"
        sha256sum "$file" | tee -a "$REPORT"

        grep_file "$file" \
            '^(FROM|WORKDIR|COPY|ADD|RUN|USER|ENV|EXPOSE|HEALTHCHECK|CMD|ENTRYPOINT)'
    fi
done

section "7. NGINX AUTHORITY"

for file in \
    docker/nginx/Dockerfile \
    docker/nginx/conf.d/default.conf \
    docker/nginx/conf.d/cmep.conf \
    nginx/nginx.conf \
    nginx/default.conf
do
    if [ -f "$file" ]; then
        echo "PRESENT_NGINX_ARTIFACT=$file" | tee -a "$REPORT"
        sha256sum "$file" | tee -a "$REPORT"
        grep_file "$file" \
            'server[[:space:]]*\{|listen[[:space:]]|proxy_pass|upstream|ssl|health|location[[:space:]]'
    fi
done

section "8. COMPOSE AUTHORITY INVENTORY"

find . \
    -maxdepth 4 \
    -type f \
    \( \
        -name 'docker-compose*.yml' \
        -o -name 'docker-compose*.yaml' \
    \) \
    -not -path './.git/*' \
    -not -path './node_modules/*' \
    -not -path './audit-output/*' \
    | sort \
    | tee -a "$REPORT"

COMPOSE_COUNT="$(
    find . \
        -maxdepth 4 \
        -type f \
        \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' \) \
        -not -path './.git/*' \
        -not -path './node_modules/*' \
        -not -path './audit-output/*' \
        | wc -l
)"

echo "COMPOSE_COUNT=$COMPOSE_COUNT" | tee -a "$REPORT"

if [ "$COMPOSE_COUNT" -eq 0 ]; then
    fail "No compose file found"
fi

section "9. COMPOSE PRODUCTION SIGNALS"

for file in \
    docker-compose.production.yml \
    docker-compose.production.yaml \
    docker-compose.yml
do
    if [ -f "$file" ]; then
        echo | tee -a "$REPORT"
        echo "### COMPOSE=$file" | tee -a "$REPORT"

        grep -nE \
            'services:|build:|image:|container_name:|ports:|expose:|environment:|env_file:|depends_on:|healthcheck:|volumes:|networks:|restart:|command:|entrypoint:' \
            "$file" \
            2>/dev/null \
            | head -n 500 \
            | tee -a "$REPORT" || true
    fi
done

section "10. DEPLOY SCRIPT AUTHORITY"

if [ -f scripts/deploy.sh ]; then
    pass "scripts/deploy.sh exists"
    sha256sum scripts/deploy.sh | tee -a "$REPORT"

    show_file scripts/deploy.sh 420
else
    fail "scripts/deploy.sh missing"
fi

section "11. DEPLOY SCRIPT PATH REFERENCES"

if [ -f scripts/deploy.sh ]; then
    grep -nE \
        'docker|compose|Dockerfile|app/|backend/|frontend/|apps/web|nginx|production|\.env|image|build|push|pull|migrate|alembic' \
        scripts/deploy.sh \
        2>/dev/null \
        | head -n 500 \
        | tee -a "$REPORT" || true
fi

section "12. CI AUTHORITY"

for file in .github/workflows/*.yml .github/workflows/*.yaml; do
    [ -f "$file" ] || continue

    echo | tee -a "$REPORT"
    echo "### CI=$file" | tee -a "$REPORT"

    grep -nE \
        'docker build|docker compose|docker-compose|Dockerfile|deploy|production|push|registry|build:|pytest|npm run|pnpm|yarn|alembic|migrate' \
        "$file" \
        2>/dev/null \
        | head -n 500 \
        | tee -a "$REPORT" || true
done

section "13. CI DOCKERFILE EXISTENCE CROSS-CHECK"

CI_DOCKERFILES="$(
    grep -RhoE \
        --include='*.yml' \
        --include='*.yaml' \
        --exclude-dir=.git \
        '(-f[[:space:]]+|Dockerfile[[:space:]]+)[^[:space:]]+Dockerfile' \
        .github 2>/dev/null \
        | head -n 100 || true
)"

echo "$CI_DOCKERFILES" | tee -a "$REPORT"

for file in \
    Dockerfile \
    backend/Dockerfile \
    worker/Dockerfile \
    frontend/Dockerfile \
    docker/backend/Dockerfile \
    docker/frontend/Dockerfile
do
    if [ -f "$file" ]; then
        echo "CI_CANDIDATE_DOCKERFILE_PRESENT=$file" | tee -a "$REPORT"
    fi
done

section "14. PRODUCTION ENV AUTHORITY"

for file in \
    .env.production \
    .env.compose \
    .env
do
    if [ -f "$file" ]; then
        echo | tee -a "$REPORT"
        echo "### ENV=$file" | tee -a "$REPORT"

        grep -nE \
            '^[A-Za-z_][A-Za-z0-9_]*=' \
            "$file" \
            2>/dev/null \
            | sed -E 's/=.*$/=<REDACTED>/' \
            | sort \
            | tee -a "$REPORT"
    fi
done

section "15. PRODUCTION ENV REFERENCES"

for target in \
    docker \
    scripts \
    app \
    apps/web \
    .github
do
    if [ -e "$target" ]; then
        grep -RInE \
            '\.env\.production|\.env\.compose|env_file:|environment:|ENV_FILE|DATABASE_URL|JWT_SECRET_KEY|ACCESS_TOKEN_EXPIRE_MINUTES|REFRESH_TOKEN_EXPIRE_DAYS' \
            "$target" \
            --exclude-dir=node_modules \
            --exclude-dir=.next \
            --exclude-dir=.venv \
            --exclude-dir=__pycache__ \
            --exclude-dir=.git \
            2>/dev/null \
            | head -n 500 \
            | sed -E \
                's/(JWT_SECRET_KEY[=:])[^[:space:]]+/\1<REDACTED>/g;
                 s/(SECRET_KEY[=:])[^[:space:]]+/\1<REDACTED>/g;
                 s/(PASSWORD[=:])[^[:space:]]+/\1<REDACTED>/g' \
            | tee -a "$REPORT" || true
    fi
done

section "16. DATABASE AUTHORITY"

echo "Alembic configuration:" | tee -a "$REPORT"

if [ -f alembic.ini ]; then
    grep -nE \
        'script_location|sqlalchemy.url|prepend_sys_path|version_path_separator' \
        alembic.ini \
        | tee -a "$REPORT"
fi

echo | tee -a "$REPORT"
echo "Database/migration directories:" | tee -a "$REPORT"

for path in \
    alembic \
    migrations \
    app/shared/infrastructure/db
do
    if [ -d "$path" ]; then
        echo "PRESENT_DB_SURFACE=$path" | tee -a "$REPORT"
        find "$path" -maxdepth 3 -type f | sort | head -n 300 | tee -a "$REPORT"
    fi
done

section "17. SOURCE PATH MISMATCH DETECTION"

MISMATCH_COUNT=0

check_reference() {
    local file="$1"
    local badpath="$2"

    if [ -f "$file" ] && grep -qF "$badpath" "$file" 2>/dev/null; then
        MISMATCH_COUNT=$((MISMATCH_COUNT + 1))
        echo "PATH_MISMATCH file=$file reference=$badpath" | tee -a "$REPORT"
    fi
}

check_reference docker/backend/Dockerfile "backend/"
check_reference docker/backend/Dockerfile "frontend/"
check_reference docker/frontend/Dockerfile "frontend/"
check_reference docker/frontend/Dockerfile "backend/"
check_reference scripts/deploy.sh "backend/"
check_reference scripts/deploy.sh "frontend/"

echo "PATH_MISMATCH_COUNT=$MISMATCH_COUNT" | tee -a "$REPORT"

if [ "$MISMATCH_COUNT" -eq 0 ]; then
    pass "No direct legacy backend/frontend path mismatch detected"
else
    review "Production path mismatch signals detected"
fi

section "18. AUTHORITATIVE PATH SUMMARY"

echo "PRODUCTION_AUTHORITY_BACKEND=app" | tee -a "$REPORT"
echo "PRODUCTION_AUTHORITY_FRONTEND=apps/web" | tee -a "$REPORT"

if [ -f docker/backend/Dockerfile ]; then
    echo "PRODUCTION_AUTHORITY_BACKEND_DOCKERFILE=docker/backend/Dockerfile" | tee -a "$REPORT"
else
    echo "PRODUCTION_AUTHORITY_BACKEND_DOCKERFILE=UNRESOLVED" | tee -a "$REPORT"
    review "Backend Dockerfile authority unresolved"
fi

if [ -f docker/frontend/Dockerfile ]; then
    echo "PRODUCTION_AUTHORITY_FRONTEND_DOCKERFILE=docker/frontend/Dockerfile" | tee -a "$REPORT"
else
    echo "PRODUCTION_AUTHORITY_FRONTEND_DOCKERFILE=UNRESOLVED" | tee -a "$REPORT"
    review "Frontend Dockerfile authority unresolved"
fi

if [ -f docker/nginx/Dockerfile ]; then
    echo "PRODUCTION_AUTHORITY_NGINX_DOCKERFILE=docker/nginx/Dockerfile" | tee -a "$REPORT"
else
    echo "PRODUCTION_AUTHORITY_NGINX_DOCKERFILE=UNRESOLVED" | tee -a "$REPORT"
    review "Nginx Dockerfile authority unresolved"
fi

if [ -f docker-compose.production.yml ]; then
    echo "PRODUCTION_AUTHORITY_COMPOSE=docker-compose.production.yml" | tee -a "$REPORT"
    pass "Production compose authority resolved"
elif [ -f docker-compose.production.yaml ]; then
    echo "PRODUCTION_AUTHORITY_COMPOSE=docker-compose.production.yaml" | tee -a "$REPORT"
    pass "Production compose authority resolved"
else
    echo "PRODUCTION_AUTHORITY_COMPOSE=UNRESOLVED" | tee -a "$REPORT"
    review "Production compose authority unresolved"
fi

if [ -f scripts/deploy.sh ]; then
    echo "PRODUCTION_AUTHORITY_DEPLOY=scripts/deploy.sh" | tee -a "$REPORT"
else
    echo "PRODUCTION_AUTHORITY_DEPLOY=UNRESOLVED" | tee -a "$REPORT"
    review "Deployment authority unresolved"
fi

echo "PRODUCTION_AUTHORITY_CI=.github/workflows/ci.yml" | tee -a "$REPORT"

section "19. R3.11 CONTINUITY CHECK"

echo "R3_11_EXPECTED_STATUS=CLOSED" | tee -a "$REPORT"

for file in \
    app/core/config.py \
    app/shared/infrastructure/security/jwt_service.py
do
    if [ -f "$file" ]; then
        echo "RUNTIME_HASH=$file" | tee -a "$REPORT"
        sha256sum "$file" | tee -a "$REPORT"
    else
        fail "R3.11 runtime authority file missing: $file"
    fi
done

LEGACY_COUNT="$(
    grep -RIlE \
        'JWT_ACCESS_TOKEN_EXPIRES_MINUTES|JWT_REFRESH_TOKEN_EXPIRES_DAYS' \
        app \
        apps/web \
        docker \
        scripts \
        docs \
        README.md \
        2>/dev/null \
        | wc -l
)"

echo "CURRENT_RUNTIME_RELEVANT_LEGACY_FILES=$LEGACY_COUNT" | tee -a "$REPORT"

if [ "$LEGACY_COUNT" -eq 0 ]; then
    pass "R3.11 legacy TTL remains absent from active production-relevant surfaces"
else
    review "R3.11 legacy TTL reference detected"
fi

section "20. SAFETY ATTESTATION"

echo "READ_ONLY=YES" | tee -a "$REPORT"
echo "NO_SOURCE_WRITES=YES" | tee -a "$REPORT"
echo "NO_RUNTIME_EXECUTION=YES" | tee -a "$REPORT"
echo "NO_ENV_EXECUTION=YES" | tee -a "$REPORT"
echo "NO_BUILD=YES" | tee -a "$REPORT"
echo "NO_DEPLOYMENT=YES" | tee -a "$REPORT"
echo "NO_DELETIONS=YES" | tee -a "$REPORT"
echo "BOUNDED_SCAN=YES" | tee -a "$REPORT"

section "21. FINAL"

echo "FAILURE_COUNT=$FAILURE_COUNT" | tee -a "$REPORT"
echo "REVIEW_COUNT=$REVIEW_COUNT" | tee -a "$REPORT"

if [ "$FAILURE_COUNT" -eq 0 ] && [ "$REVIEW_COUNT" -eq 0 ]; then
    echo "P0_01_R2_STATUS=CLEAN" | tee -a "$REPORT"
    echo "RESULT=P0_01_R2_PRODUCTION_AUTHORITY_RESOLVED" | tee -a "$REPORT"
    echo "EXIT_CODE=0" | tee -a "$REPORT"
    exit 0
elif [ "$FAILURE_COUNT" -eq 0 ]; then
    echo "P0_01_R2_STATUS=REVIEW" | tee -a "$REPORT"
    echo "RESULT=P0_01_R2_PRODUCTION_AUTHORITY_REVIEW_REQUIRED" | tee -a "$REPORT"
    echo "EXIT_CODE=10" | tee -a "$REPORT"
    exit 10
else
    echo "P0_01_R2_STATUS=FAIL" | tee -a "$REPORT"
    echo "RESULT=P0_01_R2_PRODUCTION_AUTHORITY_RESOLUTION_FAILED" | tee -a "$REPORT"
    echo "EXIT_CODE=20" | tee -a "$REPORT"
    exit 20
fi
