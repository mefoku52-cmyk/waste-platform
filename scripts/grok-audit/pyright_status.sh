#!/usr/bin/env bash
set -eu
cd "$HOME/waste-platform"
echo "===== REDIS ====="
redis-cli ping || true
echo "===== API ====="
curl -sS -o /dev/null -w "API=%{http_code}\n" --max-time 3 http://127.0.0.1:8001/health || echo API=DOWN
echo "===== WEB ====="
curl -sS -o /dev/null -w "WEB=%{http_code}\n" --max-time 3 http://127.0.0.1:3001/login || echo WEB=DOWN
echo "===== PYRIGHT ERRORS ONLY ====="
pyright --ignoreexternal --level error \
  app/modules/auth \
  app/modules/compliance \
  app/modules/documents \
  2>&1 | tail -n 40
echo "===== FILE SIZES ====="
wc -l \
  app/modules/auth/domain/entities.py \
  app/modules/auth/infrastructure/mappers.py \
  app/modules/auth/infrastructure/repositories.py \
  app/modules/compliance/infrastructure/models.py \
  app/modules/documents/infrastructure/models.py
