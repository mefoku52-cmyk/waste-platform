#!/usr/bin/env bash
set -Eeuo pipefail

TEST_NAME="${1:-smoke-test.js}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

case "${TEST_NAME}" in
  smoke|smoke-test.js) SCRIPT="smoke-test.js" ;;
  load|load-test.js) SCRIPT="load-test.js" ;;
  breakpoint|breakpoint-test.js) SCRIPT="breakpoint-test.js" ;;
  *) SCRIPT="${TEST_NAME}" ;;
esac

docker compose -f infra/docker-compose.load.yml run --rm \
  -e BASE_URL="${BASE_URL}" \
  k6 run "/scripts/${SCRIPT}"
