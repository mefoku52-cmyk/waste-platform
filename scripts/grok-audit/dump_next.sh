#!/usr/bin/env bash
set -eu
export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:32376}"
OUT="${1:-$HOME/waste-platform/scripts/grok-audit/next_evidence.txt}"
{
  echo "===== META ====="
  echo "DATE=$(date -Iseconds 2>/dev/null || date)"
  echo "HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo no-git)"
  echo "BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo no-git)"
  echo

  echo "===== GIT THREE FILES ====="
  git status --short -- \
    app/core/config.py \
    app/main.py \
    app/modules/auth/application/password_reset.py \
    || true
  echo
  git diff --stat -- \
    app/core/config.py \
    app/main.py \
    app/modules/auth/application/password_reset.py \
    || true
  echo

  echo "===== CONFIG POST_INIT COUNT ====="
  grep -n "def model_post_init" app/core/config.py || true
  echo "HAS_DEAD_GETATTR=$(grep -c 'getattr(self, \"REDIS_URL\"' app/core/config.py || true)"
  echo "HAS_LIVE_REDIS=$(grep -c 'enabled\": bool(redis_url)' app/core/config.py || true)"
  echo "HEALTH_LEAK=$(grep -c database_url app/main.py || true)"
  echo "FRONTEND_LINE=$(grep -n frontend_url app/modules/auth/application/password_reset.py || true)"
  echo

  echo "===== CONTAINER SETTINGS + REDIS KEYS ====="
  docker exec cmep-api-redis-debug python3 -c '
from app.core.config import settings
print("REDIS_URL", settings.redis.url)
print("ENABLED", settings.redis.enabled)
print("ENV", settings.app_env)
print("HEALTH_SRC_OK", "database_url" not in open("/app/app/main.py").read())
from redis import Redis
r = Redis.from_url(settings.redis.url, decode_responses=True)
print("PING", r.ping())
keys = r.keys("pwdreset:*")
print("PWDRESET_KEY_COUNT", len(keys))
'
  echo
  echo "===== END ====="
} > "$OUT"
echo "WROTE $OUT"
wc -c "$OUT"
