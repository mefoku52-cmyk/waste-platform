#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/data/data/com.termux/files/home/waste-platform}"

cd "$PROJECT_DIR" || exit 1

echo "=== CMEP REGISTRY AUTHORITY CHECK ==="
echo

echo "=== 1. GIT REMOTE ==="
git remote -v 2>/dev/null || true

echo
echo "=== 2. CURRENT COMMIT ==="
git rev-parse HEAD 2>/dev/null || true

echo
echo "=== 3. REGISTRY REFERENCES ==="

grep -RInE \
    'ghcr\.io|docker\.io|REGISTRY_IMAGE_PREFIX|docker login|docker push|docker build.*-t|build-push-action|images:' \
    .github \
    .production-release \
    scripts \
    docker-compose.yml \
    2>/dev/null |
    grep -vE \
        '\.git/|node_modules/|\.next/|__pycache__/|reports/|analyze_waste_platform' |
    head -n 250 || true

echo
echo "=== 4. GITHUB WORKFLOWS ==="

if [ -d ".github/workflows" ]; then
    find .github/workflows -maxdepth 1 -type f -print 2>/dev/null |
        sort
else
    echo "[MISSING] .github/workflows"
fi

echo
echo "=== 5. PRODUCTION RELEASE EXAMPLES ==="

grep -RInE \
    'REGISTRY_IMAGE_PREFIX|ghcr\.io|docker\.io' \
    .production-release \
    2>/dev/null |
    head -n 150 || true

echo
echo "=== 6. CURRENT PRODUCTION VALUE ==="

if grep -q '^REGISTRY_IMAGE_PREFIX=' .env.production 2>/dev/null; then
    value="$(grep '^REGISTRY_IMAGE_PREFIX=' .env.production | head -n1 | cut -d= -f2-)"

    if [ -n "$value" ]; then
        echo "REGISTRY_IMAGE_PREFIX_DEFINED=1"
        echo "REGISTRY_IMAGE_PREFIX=$value"
    else
        echo "REGISTRY_IMAGE_PREFIX_DEFINED=0"
        echo "REGISTRY_IMAGE_PREFIX_EMPTY=1"
    fi
else
    echo "REGISTRY_IMAGE_PREFIX_DEFINED=0"
fi

echo
echo "=== 7. INFERRED FROM GIT REMOTE ==="

REMOTE="$(git remote get-url origin 2>/dev/null || true)"

case "$REMOTE" in
    https://github.com/*/*.git)
        OWNER_REPO="${REMOTE#https://github.com/}"
        OWNER_REPO="${OWNER_REPO%.git}"
        OWNER="${OWNER_REPO%%/*}"
        REPO="${OWNER_REPO#*/}"

        echo "GITHUB_OWNER=$OWNER"
        echo "GITHUB_REPOSITORY=$REPO"
        echo "INFERRED_GHCR_PREFIX=ghcr.io/$OWNER"
        ;;
    git@github.com:*/*.git)
        OWNER_REPO="${REMOTE#git@github.com:}"
        OWNER_REPO="${OWNER_REPO%.git}"
        OWNER="${OWNER_REPO%%/*}"
        REPO="${OWNER_REPO#*/}"

        echo "GITHUB_OWNER=$OWNER"
        echo "GITHUB_REPOSITORY=$REPO"
        echo "INFERRED_GHCR_PREFIX=ghcr.io/$OWNER"
        ;;
    *)
        echo "GITHUB_REMOTE_UNRECOGNIZED=1"
        ;;
esac

echo
echo "=== RESULT ==="
echo "REGISTRY_AUTHORITY_CHECK=COMPLETE"
echo "NO_FILES_MODIFIED=1"
