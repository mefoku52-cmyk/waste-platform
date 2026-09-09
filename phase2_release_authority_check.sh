#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

REPO="$HOME/waste-platform"
cd "$REPO"

SHA="$(git rev-parse HEAD)"
REGISTRY="ghcr.io/mefoku52-cmyk"
TAG="release-${SHA}"

PASS=0
FAIL=0
WARN=0

pass() { PASS=$((PASS+1)); printf '[PASS] %s\n' "$1"; }
fail() { FAIL=$((FAIL+1)); printf '[FAIL] %s\n' "$1"; }
warn() { WARN=$((WARN+1)); printf '[WARN] %s\n' "$1"; }

echo "============================================================"
echo "RELEASE AUTHORITY CHECK"
echo "============================================================"
echo "HEAD=$SHA"
echo "TAG=$TAG"
echo

echo "=== 1. GIT ==="

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  pass "Git HEAD valid"
else
  fail "Git HEAD invalid"
fi

if [ "$(git branch --show-current)" = "main" ]; then
  pass "Current branch is main"
else
  warn "Current branch is $(git branch --show-current)"
fi

echo
echo "=== 2. GITHUB RELEASE RUN ==="

RUN_JSON="$(gh run view 34217821553 --json databaseId,status,conclusion,headSha,url)"

echo "$RUN_JSON"

RUN_STATUS="$(printf '%s' "$RUN_JSON" | jq -r '.status')"
RUN_CONCLUSION="$(printf '%s' "$RUN_JSON" | jq -r '.conclusion')"
RUN_SHA="$(printf '%s' "$RUN_JSON" | jq -r '.headSha')"

if [ "$RUN_STATUS" = "completed" ] && [ "$RUN_CONCLUSION" = "success" ]; then
  pass "Release run completed successfully"
else
  fail "Release run is not successful"
fi

if [ "$RUN_SHA" = "$SHA" ]; then
  pass "Release run SHA matches local HEAD"
else
  fail "Release SHA mismatch: run=$RUN_SHA local=$SHA"
fi

echo
echo "=== 3. GHCR PACKAGE VISIBILITY ==="

for image in cmep-api cmep-worker cmep-web; do
  echo
  echo "--- $image ---"

  if gh api \
    repos/mefoku52-cmyk/waste-platform/packages/container/$image \
    --jq '{name:name,visibility:visibility,package_type:package_type}' \
    2>/dev/null; then
    pass "$image GHCR package is visible through GitHub API"
  else
    warn "$image package metadata unavailable through GitHub API"
  fi
done

echo
echo "=== 4. GHCR TAG CHECK VIA GITHUB API ==="

for image in cmep-api cmep-worker cmep-web; do
  echo
  echo "--- $image:$TAG ---"

  if gh api \
    "repos/mefoku52-cmyk/waste-platform/packages/container/$image/versions" \
    --paginate \
    --jq '.[].metadata.container.tags[]?' \
    2>/dev/null | grep -Fxq "$TAG"; then
    pass "$image has exact release tag $TAG"
  else
    warn "$image exact tag not visible through GitHub package API"
  fi
done

echo
echo "=== 5. COMPOSE AUTHORITY FILES ==="

echo "--- .env.production relevant variables ---"

for key in REGISTRY_IMAGE_PREFIX IMAGE_TAG RELEASE_ID; do
  if grep -Eq "^${key}=" .env.production 2>/dev/null; then
    grep -E "^${key}=" .env.production
  else
    echo "${key}=<MISSING>"
  fi
done

echo
echo "--- docker-compose.yml image authority ---"
grep -nE 'image:|REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID' \
  docker-compose.yml || true

echo
echo "=== 6. EXPECTED RELEASE VALUES ==="

echo "REGISTRY_IMAGE_PREFIX=$REGISTRY"
echo "IMAGE_TAG=$TAG"
echo "RELEASE_ID=sha-$SHA"

echo
echo "=== 7. TEMP DIRECTORY TEST ==="

TMPFILE="$REPO/.phase2-compose-test.$$"

if printf 'test\n' > "$TMPFILE" 2>/dev/null; then
  rm -f "$TMPFILE"
  pass "Repository is writable"
else
  fail "Repository is not writable"
fi

echo
echo "=== 8. COMPOSE CONFIG WITH EXPLICIT RELEASE AUTHORITY ==="

export REGISTRY_IMAGE_PREFIX="$REGISTRY"
export IMAGE_TAG="$TAG"
export RELEASE_ID="sha-$SHA"

COMPOSE_OUT="$REPO/.phase2-compose-config.$$"
COMPOSE_ERR="$REPO/.phase2-compose-error.$$"

if docker compose config >"$COMPOSE_OUT" 2>"$COMPOSE_ERR"; then
  pass "docker compose config succeeds with exact release identity"

  echo
  echo "--- resolved images ---"
  grep -nE 'image: ghcr.io/mefoku52-cmyk/cmep-' "$COMPOSE_OUT" || true
else
  fail "docker compose config fails with exact release identity"

  echo
  echo "--- compose error ---"
  cat "$COMPOSE_ERR"
fi

rm -f "$COMPOSE_OUT" "$COMPOSE_ERR"

echo
echo "=== 9. DEPLOY SCRIPT SAFETY ==="

if [ -x scripts/deploy.sh ]; then
  pass "scripts/deploy.sh exists and is executable"
else
  warn "scripts/deploy.sh missing or not executable"
fi

echo
echo "--- deploy.sh release variables ---"
grep -nE 'REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID|docker compose|docker pull|docker compose up' \
  scripts/deploy.sh 2>/dev/null || true

echo
echo "============================================================"
echo "FINAL RESULT"
echo "============================================================"
echo "PASS=$PASS"
echo "FAIL=$FAIL"
echo "WARN=$WARN"
echo "RELEASE_SHA=$SHA"
echo "RELEASE_TAG=$TAG"

if [ "$FAIL" -eq 0 ]; then
  echo "PHASE2_VERDICT=PASS"
else
  echo "PHASE2_VERDICT=FAIL"
fi
