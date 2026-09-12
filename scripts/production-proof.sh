#!/bin/bash
# Production Proof Report — dôkaz produkčnej pripravenosti
set +e  # pokračuj aj keď niečo zlyhá

REPORT="PRODUCTION_PROOF_$(date +%Y%m%d_%H%M%S).txt"

{
echo "════════════════════════════════════════════════════════════════════════"
echo "         WASTE-PLATFORM PRODUCTION PROOF"
echo "         Generated: $(date)"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "1. PROJECT STRUCTURE"
echo "════════════════════════════════════════════════════════════════════════"
echo "Project size (excl. node_modules, .venv, .git):"
du -sh --exclude=node_modules --exclude=.venv --exclude=.git . 2>/dev/null | head -1
echo ""
echo "Top-level structure:"
ls -la | grep -vE "^total|^d.*\s\.$|^d.*\s\.\.$" | awk '{print "  " $NF}' | sort
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "2. STATIC ANALYSIS"
echo "════════════════════════════════════════════════════════════════════════"
echo "--- ty check (type safety) ---"
ty check 2>&1 | tail -3
echo ""
echo "--- ruff format (code style) ---"
ruff format --check . 2>&1 | tail -2
echo ""
echo "--- ruff check (lint) ---"
ruff check . 2>&1 | tail -2
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "3. TEST SUITE"
echo "════════════════════════════════════════════════════════════════════════"
python3 -m pytest tests/ -q --no-header 2>&1 | tail -10
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "4. COVERAGE SUMMARY"
echo "════════════════════════════════════════════════════════════════════════"
python3 -m pytest tests/ -q --no-header --cov=app 2>&1 | grep -E "TOTAL|passed|failed" | tail -3
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "5. BACKEND HEALTH CHECK"
echo "════════════════════════════════════════════════════════════════════════"
echo "FastAPI routes count:"
python3 -c "from app.main import app; print(f'  {len(app.routes)} routes registered')" 2>&1 | tail -1
echo ""
echo "Route list:"
python3 -c "
from app.main import app
for r in app.routes:
    if hasattr(r, 'methods') and hasattr(r, 'path'):
        methods = ','.join(sorted(r.methods - {'HEAD', 'OPTIONS'})) or 'MOUNT'
        print(f'  {methods:15s} {r.path}')
" 2>&1 | head -25
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "6. ALEMBIC MIGRATIONS"
echo "════════════════════════════════════════════════════════════════════════"
echo "Migration heads:"
alembic heads 2>&1 | tail -2
echo ""
echo "Migration history:"
alembic history 2>&1 | tail -5
echo ""
echo "Schema consistency check (SQLite):"
DATABASE_URL="sqlite+aiosqlite:///./proof_check.db" alembic upgrade head 2>&1 | tail -1
DATABASE_URL="sqlite+aiosqlite:///./proof_check.db" alembic check 2>&1 | tail -1
rm -f proof_check.db
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "7. FRONTEND"
echo "════════════════════════════════════════════════════════════════════════"
echo "Next.js build artifacts:"
ls -la apps/web/.next/ 2>/dev/null | head -5 || echo "  (no build yet — run 'npm run build' first)"
echo ""
echo "Frontend dependencies:"
cat apps/web/package.json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  name: {d.get(\"name\")}')
print(f'  version: {d.get(\"version\")}')
print(f'  scripts: {list(d.get(\"scripts\", {}).keys())}')
print(f'  dependencies: {len(d.get(\"dependencies\", {}))}')
print(f'  devDependencies: {len(d.get(\"devDependencies\", {}))}')
"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "8. DOCKER & DEPLOYMENT"
echo "════════════════════════════════════════════════════════════════════════"
echo "Dockerfiles present:"
find . -name "Dockerfile" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./apps/web/node_modules/*" 2>/dev/null | sort
echo ""
echo "docker-compose.yml validation:"
docker compose config --quiet 2>&1 && echo "  ✅ Compose syntax OK" || echo "  ❌ Compose syntax FAIL"
echo ""
echo "Makefile targets:"
make help 2>&1 | head -15
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "9. GIT REPOSITORY"
echo "════════════════════════════════════════════════════════════════════════"
echo "Current branch:"
git branch --show-current
echo ""
echo "Git status:"
git status --short | head -5
echo "  Uncommitted: $(git status --short | wc -l)"
echo ""
echo "Recent commits (last 15):"
git log --oneline -15
echo ""
echo "Branches:"
git branch -a | head -5
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "10. CODE QUALITY METRICS"
echo "════════════════════════════════════════════════════════════════════════"
echo "Python files:"
find app -name "*.py" -not -path "*/__pycache__/*" | wc -l
echo ""
echo "Test files:"
find tests -name "test_*.py" -not -path "*/__pycache__/*" | wc -l
echo ""
echo "Test count:"
python3 -m pytest tests/ --collect-only -q 2>&1 | tail -1
echo ""
echo "Dead code check (unused imports in app):"
grep -rn "from.*import.*# noqa: F401" app/ 2>/dev/null | wc -l
echo "  (should be low — most are register_models.py)"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "11. AI-GENERATED BALAST CHECK"
echo "════════════════════════════════════════════════════════════════════════"
echo "Backup files (.bak, .old, .backup):"
find . \( -name "*.bak" -o -name "*.bak.*" -o -name "*.old" -o -name "*.backup*" -o -name "*.orig" \) -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./.git/*" -not -path "./apps/web/node_modules/*" -not -path "./apps/web/.next/*" 2>/dev/null | head -10 || echo "  ✅ None found"
echo ""
echo "AI script directories (should be empty):"
ls -d scripts/grok-audit scripts/fixes scripts/forensics scripts/legacy 2>/dev/null || echo "  ✅ None found"
echo ""
echo "Placeholder/TODO in production code:"
grep -rn "TODO\|FIXME\|XXX\|placeholder" app/ --include="*.py" 2>/dev/null | grep -v "__pycache__" | grep -v "register_models\|_is_placeholder" | head -5 || echo "  ✅ None found"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "12. SECURITY CHECK"
echo "════════════════════════════════════════════════════════════════════════"
echo ".env files in git (should be only .env.example):"
git ls-files | grep -E "^\.env" || echo "  ✅ Only .env.example tracked"
echo ""
echo "Hardcoded secrets scan:"
grep -rn "password.*=.*['\"][^'\"]\{8,\}['\"]" app/ --include="*.py" 2>/dev/null | grep -v "password_hash\|hashed\|test_\|example" | head -5 || echo "  ✅ None found"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo "                    END OF PRODUCTION PROOF"
echo "════════════════════════════════════════════════════════════════════════"

} > "$REPORT" 2>&1

echo "✅ Report generated: $REPORT"
echo ""
echo "Size: $(wc -l < "$REPORT") lines"
echo "Path: $(realpath "$REPORT")"
