#!/usr/bin/env bash
set -u

cd ~/waste-platform || exit 1

SHA="$(git rev-parse HEAD 2>/dev/null || true)"
REG="ghcr.io/mefoku52-cmyk"
TAG="release-$SHA"

echo "=== R60/R65 10-STEP READ-ONLY FORENSIC ==="
echo "SHA=${SHA:0:12}..."
echo "TAG=${TAG:0:24}..."
echo

# 1. ACTIVE CI
echo "[01] ACTIVE CI"
if [ -f .github/workflows/ci.yml ]; then
    echo "CI=FOUND"
    grep -nE 'working-directory:|docker build|docker push|build-push-action|docker/login-action|permissions:|packages:' \
        .github/workflows/ci.yml 2>/dev/null | head -n 30
else
    echo "CI=MISSING"
fi
echo

# 2. BACKEND BUILD CONTEXT
echo "[02] BACKEND BUILD CONTEXT"
grep -nE 'working-directory:|docker build.*Dockerfile' \
    .github/workflows/ci.yml 2>/dev/null | grep -E 'app|backend|Dockerfile' | head -n 15
echo "app/Dockerfile COPY:"
grep -nE '^COPY ' app/Dockerfile 2>/dev/null | head -n 10
echo

# 3. API DOCKERFILE AUTHORITY
echo "[03] API DOCKERFILE AUTHORITY"
if [ -f app/Dockerfile ]; then echo "app/Dockerfile=FOUND"; fi
if [ -f docker/backend/Dockerfile ]; then echo "docker/backend/Dockerfile=FOUND"; fi
echo "AUTHORITY:"
grep -nE 'Backend app|Backend image' docs/AUTHORITY.md 2>/dev/null || true
echo

# 4. WEB DOCKERFILE AUTHORITY
echo "[04] WEB DOCKERFILE AUTHORITY"
if [ -f apps/web/Dockerfile ]; then echo "apps/web/Dockerfile=FOUND"; fi
if [ -f docker/frontend/Dockerfile ]; then echo "docker/frontend/Dockerfile=FOUND"; fi
echo "AUTHORITY:"
grep -nE 'Frontend app|Frontend image' docs/AUTHORITY.md 2>/dev/null || true
echo

# 5. GHCR PUBLISH MECHANISM
echo "[05] GHCR PUBLISH"
if grep -RInE \
    'docker[[:space:]]+push|docker/login-action|docker/build-push-action|build-push-action|push:[[:space:]]*true' \
    .github/workflows 2>/dev/null | grep -q .; then
    echo "PUBLISHER=FOUND"
else
    echo "PUBLISHER=NOT_FOUND"
fi
grep -RInE \
    'ghcr\.io|packages:[[:space:]]*write|GITHUB_TOKEN' \
    .github/workflows 2>/dev/null | head -n 20
echo

# 6. IMMUTABLE RELEASE TAG
echo "[06] RELEASE TAG"
if grep -RInE \
    'release-\$\{\{[[:space:]]*github\.sha|release-\$\{GITHUB_SHA\}' \
    .github/workflows 2>/dev/null | grep -q .; then
    echo "CI_RELEASE_TAG=FOUND"
else
    echo "CI_RELEASE_TAG=NOT_FOUND"
fi
echo "EXPECTED_RELEASE_ID=sha-$SHA"
echo "EXPECTED_IMAGE_TAG=$TAG"
echo

# 7. WORKFLOW PERMISSIONS / SYNTAX EVIDENCE
echo "[07] ACTIONS PERMISSIONS"
grep -RInE \
    '^[[:space:]]*permissions:|packages:[[:space:]]*write|contents:[[:space:]]*write' \
    .github/workflows 2>/dev/null | head -n 20 || echo "EXPLICIT_PERMISSIONS=NOT_FOUND"

if command -v gh >/dev/null 2>&1; then
    printf "ACTIONS_ENABLED="
    gh api repos/mefoku52-cmyk/waste-platform/actions/permissions \
        --jq '.enabled' 2>/dev/null || echo "UNKNOWN"
fi
echo

# 8. GHCR RELEASE EXISTENCE
echo "[08] GHCR RELEASE EXISTENCE"
for IMG in cmep-api cmep-web; do
    CODE="$(curl -sS -o /dev/null -w '%{http_code}' \
        -H 'Accept: application/vnd.oci.image.manifest.v1+json' \
        "https://ghcr.io/v2/mefoku52-cmyk/$IMG/manifests/$TAG" \
        2>/dev/null || echo 000)"
    echo "$IMG=HTTP_$CODE"
done
echo

# 9. REMOTE RELEASE TAG + LOCAL IMAGE
echo "[09] RELEASE ARTIFACT EVIDENCE"

if git ls-remote --tags origin "refs/tags/release-$SHA" 2>/dev/null | grep -q .; then
    echo "REMOTE_RELEASE_TAG=FOUND"
else
    echo "REMOTE_RELEASE_TAG=NOT_FOUND"
fi

if command -v docker >/dev/null 2>&1; then
    echo "DOCKER_HOST=${DOCKER_HOST:-DEFAULT}"
    docker info >/dev/null 2>&1 && echo "DOCKER=PASS" || echo "DOCKER=FAIL"

    for IMG in cmep-api cmep-web; do
        if docker image inspect "$REG/$IMG:$TAG" >/dev/null 2>&1; then
            echo "LOCAL_$IMG=FOUND"
        else
            echo "LOCAL_$IMG=NOT_FOUND"
        fi
    done
fi
echo

# 10. PRODUCTION GATE
echo "[10] PRODUCTION GATE"

export REGISTRY_IMAGE_PREFIX="$REG"
export RELEASE_ID="sha-$SHA"
export IMAGE_TAG="$TAG"

if docker compose --env-file .env.production config >/dev/null 2>&1; then
    echo "COMPOSE_CONFIG=PASS"
else
    echo "COMPOSE_CONFIG=FAIL"
fi

if docker compose --env-file .env.production config 2>/dev/null |
   grep -q "$REG/cmep-api:$TAG"; then
    echo "API_IDENTITY=PASS"
else
    echo "API_IDENTITY=FAIL"
fi

if docker compose --env-file .env.production config 2>/dev/null |
   grep -q "$REG/cmep-web:$TAG"; then
    echo "WEB_IDENTITY=PASS"
else
    echo "WEB_IDENTITY=FAIL"
fi

echo
echo "=== FINAL FACTS ==="

echo "HEAD=$SHA"
echo "REGISTRY=$REG"
echo "IMAGE_TAG=$TAG"

if grep -RInE \
    'docker[[:space:]]+push|docker/login-action|docker/build-push-action|build-push-action|push:[[:space:]]*true' \
    .github/workflows 2>/dev/null | grep -q .; then
    echo "CI_PUBLISHER=FOUND"
else
    echo "CI_PUBLISHER=NOT_FOUND"
fi

if grep -RInE \
    'release-\$\{\{[[:space:]]*github\.sha|release-\$\{GITHUB_SHA\}' \
    .github/workflows 2>/dev/null | grep -q .; then
    echo "CI_RELEASE_TAG=FOUND"
else
    echo "CI_RELEASE_TAG=NOT_FOUND"
fi

echo "NO_DEPLOY_PERFORMED=1"
echo "NO_PUSH_PERFORMED=1"
echo "NO_FILES_MODIFIED_BY_AUDIT=1"
echo "=== END ==="
