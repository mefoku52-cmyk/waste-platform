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

pass() {
  PASS=$((PASS+1))
  printf '[PASS] %s\n' "$1"
}

fail() {
  FAIL=$((FAIL+1))
  printf '[FAIL] %s\n' "$1"
}

warn() {
  WARN=$((WARN+1))
  printf '[WARN] %s\n' "$1"
}

section() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

section "1. GIT RELEASE IDENTITY"

echo "REPO=$REPO"
echo "HEAD=$SHA"
echo "TAG=$TAG"

if git status --porcelain | grep -qE '^[ MADRCU?!]'; then
  warn "Working tree contains untracked/modified files"
else
  pass "Working tree clean"
fi

if git branch --show-current | grep -qx 'main'; then
  pass "Current branch is main"
else
  warn "Current branch is not main"
fi

section "2. RELEASE WORKFLOW"

if gh api repos/mefoku52-cmyk/waste-platform/actions/workflows \
  --jq '.workflows[] | select(.path==".github/workflows/release.yml") | .state' \
  | grep -qx 'active'; then
  pass "Release workflow registered and active"
else
  fail "Release workflow not registered as active"
fi

section "3. GHCR MANIFESTS"

for image in cmep-api cmep-worker cmep-web; do
  FULL="${REGISTRY}/${image}:${TAG}"

  echo
  echo "Checking: $FULL"

  if docker manifest inspect "$FULL" >/dev/null 2>&1; then
    pass "$image release manifest exists"
  else
    fail "$image release manifest missing/unreadable"
  fi
done

section "4. DOCKER DAEMON"

if docker info >/dev/null 2>&1; then
  pass "Docker daemon reachable"
else
  fail "Docker daemon unavailable"
fi

echo
docker version --format 'CLIENT={{.Client.Version}} SERVER={{.Server.Version}}' 2>/dev/null || true

section "5. COMPOSE CONFIGURATION"

if [ -f docker-compose.yml ]; then
  pass "docker-compose.yml exists"
else
  fail "docker-compose.yml missing"
fi

if [ -f .env.production ]; then
  pass ".env.production exists"
else
  warn ".env.production missing"
fi

echo
echo "--- Registry references ---"
grep -nE 'REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID' \
  docker-compose.yml .env.production 2>/dev/null || true

section "6. COMPOSE INTERPOLATION"

if docker compose config >/tmp/waste-compose-config.txt 2>/tmp/waste-compose-error.txt; then
  pass "docker compose config succeeds"
else
  fail "docker compose config FAILED"
  cat /tmp/waste-compose-error.txt
fi

echo
echo "--- Resolved services ---"
docker compose config --services 2>/dev/null || true

section "7. CURRENT CONTAINERS"

echo "--- Relevant containers ---"
docker ps -a \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' \
  | grep -E 'cmep-|NAMES' || true

section "8. CURRENT PORTS"

echo "--- Docker published ports ---"
docker ps \
  --format '{{.Names}}\t{{.Ports}}' \
  | grep -E 'cmep-|NAMES' || true

echo
echo "--- Host listeners ---"
ss -lntp 2>/dev/null || true

section "9. RC WEB CONTAINER"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-web-rc-55bc4d692766'; then
  pass "Known RC web container is running"

  echo
  echo "--- Web container ---"
  docker inspect cmep-web-rc-55bc4d692766 \
    --format 'IP={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}} PORT={{.Config.Env}}' \
    2>/dev/null || true

  echo
  echo "--- Web process ---"
  docker exec cmep-web-rc-55bc4d692766 sh -c \
    'ps aux 2>/dev/null | head -20 || true'

  echo
  echo "--- Web HTTP smoke ---"
  if docker exec cmep-web-rc-55bc4d692766 sh -c \
    'wget -q -O /dev/null --timeout=5 http://127.0.0.1:3001/'; then
    pass "RC web internal HTTP 200"
  else
    fail "RC web internal HTTP check failed"
  fi
else
  warn "Known RC web container is not currently running"
fi

section "10. API CONTAINER"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-api'; then
  pass "API container is running"

  echo
  echo "--- API inspect ---"
  docker inspect cmep-api \
    --format 'IP={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}} STATUS={{.State.Status}}' \
    2>/dev/null || true

  echo
  echo "--- API logs tail ---"
  docker logs --tail 40 cmep-api 2>&1 || true
else
  warn "API container is not currently running"
fi

section "11. REDIS"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-redis'; then
  if docker exec cmep-redis redis-cli ping 2>/dev/null | grep -qx 'PONG'; then
    pass "Redis responds PONG"
  else
    fail "Redis container does not respond PONG"
  fi
else
  warn "Redis container not running"
fi

section "12. POSTGRES"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-postgres'; then
  if docker exec cmep-postgres pg_isready >/dev/null 2>&1; then
    pass "PostgreSQL accepts readiness check"
  else
    fail "PostgreSQL readiness check failed"
  fi
else
  warn "PostgreSQL container not running"
fi

section "13. DOCKER NETWORKS"

echo "--- Networks ---"
docker network ls

echo
echo "--- Relevant container network attachments ---"
for c in cmep-api cmep-redis cmep-postgres cmep-web-rc-55bc4d692766; do
  if docker inspect "$c" >/dev/null 2>&1; then
    echo
    echo "[$c]"
    docker inspect "$c" \
      --format '{{range $name,$net := .NetworkSettings.Networks}}network={{$name}} ip={{$net.IPAddress}}{{"\n"}}{{end}}'
  fi
done

section "14. API -> REDIS CONNECTIVITY"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-api' \
  && docker ps --format '{{.Names}}' | grep -qx 'cmep-redis'; then

  API_NETS="$(docker inspect cmep-api --format '{{range $name,$net := .NetworkSettings.Networks}}{{$name}}{{"\n"}}{{end}}' | sort)"
  REDIS_NETS="$(docker inspect cmep-redis --format '{{range $name,$net := .NetworkSettings.Networks}}{{$name}}{{"\n"}}{{end}}' | sort)"

  if [ "$API_NETS" = "$REDIS_NETS" ]; then
    pass "API and Redis share network"
  else
    warn "API and Redis network sets differ"
    echo "API:"
    echo "$API_NETS"
    echo "REDIS:"
    echo "$REDIS_NETS"
  fi
fi

section "15. API -> POSTGRES CONNECTIVITY"

if docker ps --format '{{.Names}}' | grep -qx 'cmep-api' \
  && docker ps --format '{{.Names}}' | grep -qx 'cmep-postgres'; then

  if docker exec cmep-api sh -c \
    'python - <<PY
import socket
try:
    socket.gethostbyname("cmep-postgres")
    print("DNS=PASS")
except Exception as e:
    print("DNS=FAIL", e)
    raise
PY' 2>/dev/null; then
    pass "API can resolve cmep-postgres"
  else
    warn "API cannot resolve cmep-postgres"
  fi
fi

section "16. WORKER IMAGE"

if docker manifest inspect \
  "${REGISTRY}/cmep-worker:${TAG}" >/dev/null 2>&1; then
  pass "Worker release image is published"
else
  fail "Worker release image is unavailable"
fi

section "17. FINAL PHASE-1 VERDICT"

echo
echo "PASS=$PASS"
echo "FAIL=$FAIL"
echo "WARN=$WARN"
echo "RELEASE_SHA=$SHA"
echo "RELEASE_TAG=$TAG"

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "PHASE1_VERDICT=PASS"
  echo "NEXT_STAGE=CONTROLLED_FULL_STACK_INTEGRATION"
else
  echo
  echo "PHASE1_VERDICT=FAIL"
  echo "NEXT_STAGE=FIX_BLOCKERS_BEFORE_INTEGRATION"
fi
