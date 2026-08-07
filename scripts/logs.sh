#!/usr/bin/env bash
set -Eeuo pipefail
SERVICE="${1:-}"
PATTERN="${2:-}"
TAIL_LINES="${TAIL_LINES:-200}"
if [ -z "${SERVICE}" ]; then
echo "Usage: $0 <service> [pattern]"
  exit 1
fi
if [ -n "${PATTERN}" ]; then
docker compose logs --tail="${TAIL_LINES}" "${SERVICE}" | grep -i --color=always "${PATTERN}" || true
else
  docker compose logs --tail="${TAIL_LINES}" "${SERVICE}"
fi
