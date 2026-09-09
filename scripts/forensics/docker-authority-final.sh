#!/usr/bin/env bash
set -u

cd ~/waste-platform || exit 1

echo "=== DOCKER AUTHORITY FORENSIC ==="

# 1. AUTHORITY CONTRACT
echo "[1] AUTHORITY"
grep -nE 'Backend app|Backend image|Frontend app|Frontend image' \
    docs/AUTHORITY.md 2>/dev/null || true

# 2. SOURCE TREES
echo
echo "[2] SOURCE TREES"
for p in \
    app \
    app/Dockerfile \
    app/requirements.txt \
    app/worker/Dockerfile \
    apps/web \
    apps/web/Dockerfile \
    apps/web/package.json \
    apps/web/package-lock.json \
    docker/backend/Dockerfile \
    docker/frontend/Dockerfile
do
    [ -e "$p" ] && echo "FOUND   $p" || echo "MISSING $p"
done

# 3. API DOCKERFILES
echo
echo "[3] API DOCKERFILES"

for f in app/Dockerfile docker/backend/Dockerfile; do
    echo "--- $f ---"
    if [ -f "$f" ]; then
        grep -nE '^FROM|^WORKDIR|^COPY|^RUN|^CMD|^ENTRYPOINT' "$f" 2>/dev/null
    else
        echo "MISSING"
    fi
done

# 4. WEB DOCKERFILES
echo
echo "[4] WEB DOCKERFILES"

for f in apps/web/Dockerfile docker/frontend/Dockerfile; do
    echo "--- $f ---"
    if [ -f "$f" ]; then
        grep -nE '^FROM|^WORKDIR|^COPY|^RUN|^CMD|^ENTRYPOINT' "$f" 2>/dev/null
    else
        echo "MISSING"
    fi
done

# 5. CI BUILD CONTEXT
echo
echo "[5] CI CONTEXT"

grep -nE \
    'working-directory:|docker build|docker/build-push-action' \
    .github/workflows/ci.yml 2>/dev/null || true

# 6. REQUIRED COPY SOURCES
echo
echo "[6] COPY SOURCE VALIDATION"

check_copy() {
    local context="$1"
    local source="$2"

    if [ -e "$context/$source" ]; then
        echo "PASS $context/$source"
    else
        echo "FAIL $context/$source"
    fi
}

echo "API app/Dockerfile with CI context=app:"
check_copy "app" "app/requirements.txt"
check_copy "app" "app"

echo
echo "API docker/backend/Dockerfile with repo context=.:"
check_copy "." "backend/requirements.txt"
check_copy "." "backend"

echo
echo "WEB apps/web/Dockerfile with context=apps/web:"
check_copy "apps/web" "package.json"
check_copy "apps/web" "package-lock.json"

echo
echo "WEB docker/frontend/Dockerfile with repo context=.:"
check_copy "." "frontend/package.json"
check_copy "." "frontend"

# 7. COMPOSE BUILD VS IMAGE
echo
echo "[7] COMPOSE"

grep -nA15 -E '^[[:space:]]+(api|web):' \
    docker-compose.yml 2>/dev/null |
    grep -E '^[0-9]+:|image:|build:|container_name:' |
    head -n 30 || true

# 8. GIT TRACKING
echo
echo "[8] GIT TRACKING"

for p in \
    app/Dockerfile \
    docker/backend/Dockerfile \
    apps/web/Dockerfile \
    docker/frontend/Dockerfile
do
    git ls-files --error-unmatch "$p" >/dev/null 2>&1 \
        && echo "TRACKED $p" \
        || echo "UNTRACKED $p"
done

# 9. HISTORICAL RELEASE EVIDENCE
echo
echo "[9] HISTORICAL BUILD EVIDENCE"

for f in \
    .production-release/r60-backup/docker-compose.yml.20260903_103811.bak \
    .production-release/r61-backup-20260903_104708/ci.yml \
    .production-release/r61-backup-20260903_104708/docker-compose.yml
do
    if [ -f "$f" ]; then
        echo "FOUND $f"
        grep -nE 'dockerfile:|context:|working-directory:|docker build' "$f" 2>/dev/null |
            head -n 15 || true
    else
        echo "MISSING $f"
    fi
done

# 10. FINAL FACTUAL RESULT
echo
echo "=== FINAL RESULT ==="

if [ -f app/Dockerfile ] &&
   grep -qE '^COPY app/requirements\.txt' app/Dockerfile &&
   grep -qE 'working-directory:[[:space:]]*app' .github/workflows/ci.yml &&
   grep -qE 'docker build.*-f Dockerfile \.' .github/workflows/ci.yml
then
    echo "BACKEND_CONTEXT_CONFLICT=CONFIRMED"
else
    echo "BACKEND_CONTEXT_CONFLICT=NOT_CONFIRMED"
fi

if [ -f docker/backend/Dockerfile ] &&
   [ ! -d backend ]; then
    echo "CANONICAL_BACKEND_DOCKERFILE=UNBUILDABLE_FROM_CURRENT_TREE"
else
    echo "CANONICAL_BACKEND_DOCKERFILE=NOT_CONFIRMED"
fi

if [ -f docker/frontend/Dockerfile ] &&
   [ ! -d frontend ]; then
    echo "CANONICAL_FRONTEND_DOCKERFILE=UNBUILDABLE_FROM_CURRENT_TREE"
else
    echo "CANONICAL_FRONTEND_DOCKERFILE=NOT_CONFIRMED"
fi

if [ -f apps/web/Dockerfile ] &&
   [ -f apps/web/package.json ] &&
   [ -f apps/web/package-lock.json ]; then
    echo "WEB_APPS_DOCKERFILE=BUILD_INPUTS_PRESENT"
else
    echo "WEB_APPS_DOCKERFILE=INPUTS_MISSING"
fi

echo "NO_BUILD_PERFORMED=1"
echo "NO_PUSH_PERFORMED=1"
echo "NO_DEPLOY_PERFORMED=1"
echo "=== END ==="
