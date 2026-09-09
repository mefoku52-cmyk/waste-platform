#!/usr/bin/env bash
set -u

cd ~/waste-platform || exit 1

echo "=== AUTHORITY CONSISTENCY FORENSIC ==="
echo "HEAD=$(git rev-parse HEAD)"
echo

echo "[1] AUTHORITY CONTRACT"
grep -nE \
  'Backend app|Backend image|Frontend app|Frontend image|Compose|Env contract' \
  docs/AUTHORITY.md 2>/dev/null || echo "AUTHORITY_ENTRIES=NOT_FOUND"
echo

echo "[2] ACTIVE CI"
grep -nE \
  'working-directory:|docker build|docker push|docker/login-action|build-push-action|permissions:|packages:' \
  .github/workflows/ci.yml 2>/dev/null || echo "CI=NOT_FOUND"
echo

echo "[3] PRODUCTION COMPOSE"
grep -nE \
  '^[[:space:]]+(api|web):|^[[:space:]]+image:|^[[:space:]]+build:|context:|dockerfile:' \
  docker-compose.yml 2>/dev/null || echo "COMPOSE=NOT_FOUND"
echo

echo "[4] API DOCKERFILES"
for f in app/Dockerfile docker/backend/Dockerfile; do
  echo "--- $f ---"
  if [ -f "$f" ]; then
    grep -nE '^FROM|^WORKDIR|^COPY|^RUN|^CMD|^ENTRYPOINT' "$f"
  else
    echo "MISSING"
  fi
done
echo

echo "[5] WEB DOCKERFILES"
for f in apps/web/Dockerfile docker/frontend/Dockerfile; do
  echo "--- $f ---"
  if [ -f "$f" ]; then
    grep -nE '^FROM|^WORKDIR|^COPY|^RUN|^CMD|^ENTRYPOINT' "$f"
  else
    echo "MISSING"
  fi
done
echo

echo "[6] SOURCE TREE"
for p in \
  app \
  app/requirements.txt \
  app/Dockerfile \
  app/worker \
  apps/web \
  apps/web/package.json \
  apps/web/package-lock.json \
  apps/web/Dockerfile \
  backend \
  frontend
do
  [ -e "$p" ] && echo "FOUND   $p" || echo "MISSING $p"
done
echo

echo "[7] GIT TRACKING"
for p in \
  app/Dockerfile \
  apps/web/Dockerfile \
  docker/backend/Dockerfile \
  docker/frontend/Dockerfile \
  docs/AUTHORITY.md \
  .github/workflows/ci.yml \
  docker-compose.yml
do
  git ls-files --error-unmatch "$p" >/dev/null 2>&1 \
    && echo "TRACKED $p" \
    || echo "UNTRACKED $p"
done
echo

echo "[8] HISTORICAL R60/R61 AUTHORITY"
for f in \
  .production-release/r60-backup/docker-compose.yml.20260903_103811.bak \
  .production-release/r61-backup-20260903_104708/ci.yml \
  .production-release/r61-backup-20260903_104708/docker-compose.yml
do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    grep -nE \
      'working-directory:|docker build|context:|dockerfile:' \
      "$f" 2>/dev/null | head -n 20
  fi
done
echo

echo "[9] ACTIVE IMAGE AUTHORITY"
grep -RInE \
  'REGISTRY_IMAGE_PREFIX|cmep-api|cmep-web|IMAGE_TAG|RELEASE_ID' \
  docker-compose.yml \
  scripts/deploy.sh \
  scripts/deploy/*.sh \
  2>/dev/null | head -n 60
echo

echo "[10] FINAL CONSISTENCY"
echo "AUTHORITY_BACKEND_APP=$(grep -q 'Backend app.*app/' docs/AUTHORITY.md 2>/dev/null && echo app/ || echo UNKNOWN)"
echo "AUTHORITY_BACKEND_DOCKERFILE=$(grep -oE 'Backend image.*`[^`]+`' docs/AUTHORITY.md 2>/dev/null | head -n1 || echo UNKNOWN)"
echo "AUTHORITY_FRONTEND_APP=$(grep -q 'Frontend app.*apps/web/' docs/AUTHORITY.md 2>/dev/null && echo apps/web/ || echo UNKNOWN)"
echo "AUTHORITY_FRONTEND_DOCKERFILE=$(grep -oE 'Frontend image.*`[^`]+`' docs/AUTHORITY.md 2>/dev/null | head -n1 || echo UNKNOWN)"

if [ -d backend ] || [ -d frontend ]; then
  echo "LEGACY_TREE_PRESENT=YES"
else
  echo "LEGACY_TREE_PRESENT=NO"
fi

if [ -f app/Dockerfile ] && [ -f apps/web/Dockerfile ]; then
  echo "INNER_APP_DOCKERFILES=PRESENT"
else
  echo "INNER_APP_DOCKERFILES=INCOMPLETE"
fi

if grep -qE 'working-directory:[[:space:]]*app' .github/workflows/ci.yml 2>/dev/null &&
   grep -qE '^COPY[[:space:]]+app/requirements\.txt' app/Dockerfile 2>/dev/null; then
  echo "BACKEND_CI_CONTEXT=CONFLICT"
else
  echo "BACKEND_CI_CONTEXT=NOT_CONFIRMED"
fi

if [ ! -d backend ] && [ -f docker/backend/Dockerfile ]; then
  echo "DOCKER_BACKEND_AUTHORITY=UNBUILDABLE"
else
  echo "DOCKER_BACKEND_AUTHORITY=NOT_CONFIRMED"
fi

if [ ! -d frontend ] && [ -f docker/frontend/Dockerfile ]; then
  echo "DOCKER_FRONTEND_AUTHORITY=UNBUILDABLE"
else
  echo "DOCKER_FRONTEND_AUTHORITY=NOT_CONFIRMED"
fi

echo "NO_BUILD=1"
echo "NO_PUSH=1"
echo "NO_DEPLOY=1"
echo "NO_MUTATION=1"
echo "=== END ==="
