#!/usr/bin/env bash
cd ~/waste-platform

echo "=== A1: datetime v auth entities ==="
grep -n "datetime" app/modules/auth/domain/entities.py || true

echo
echo "=== A2: naive datetime v celom app/ ==="
grep -rn --exclude-dir=__pycache__ "datetime\.utcnow\|datetime\.now()" app || echo "[ok] žiadne naive now"

echo
echo "=== A3: datetime v base entite ==="
grep -n "datetime" app/shared/domain/base.py || true

echo
echo "=== B1: main.py include_router ==="
grep -n "include_router\|api_router\|_router" app/main.py || true

echo
echo "=== B2: api_router.py ==="
cat app/shared/presentation/api_router.py

echo
echo "=== B3: všetky include_router v app/ ==="
grep -rn --exclude-dir=__pycache__ "include_router" app
