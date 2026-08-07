#!/usr/bin/env bash
set -Eeuo pipefail

echo "=== CMEP Project Validation Script ==="
echo "Date: $(date -Iseconds)"

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
cd "${PROJECT_DIR}"

ERRORS=0
WARNINGS=0

log_error() {
  echo "[ERROR] $1" >&2
  ((ERRORS++)) || true
}

log_warn() {
  echo "[WARN] $1"
  ((WARNINGS++)) || true
}

log_ok() {
  echo "[OK] $1"
}

# -------------------------------------------------
# 1. Check basic structure
# -------------------------------------------------
echo ""
echo "=== 1. Checking basic project structure ==="

REQUIRED_DIRS=(
  "app"
  "apps/web"
  "docs"
  "infra"
  "scripts"
)

for d in "${REQUIRED_DIRS[@]}"; do
  if [ -d "${d}" ]; then
    log_ok "Directory exists: ${d}"
  else
    log_error "Missing directory: ${d}"
  fi
done

REQUIRED_FILES=(
  "README.md"
  "docker-compose.yml"
  ".env.production"
  "app/main.py"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [ -f "${f}" ]; then
    log_ok "File exists: ${f}"
  else
    log_error "Missing file: ${f}"
  fi
done

# -------------------------------------------------
# 2. Check key module directories
# -------------------------------------------------
echo ""
echo "=== 2. Checking backend module structure ==="

MODULES=(
  "auth"
  "companies"
  "users"
  "company_memberships"
  "listings"
  "inquiries"
  "documents"
  "compliance"
  "notifications"
  "analytics"
  "admin"
)

for m in "${MODULES[@]}"; do
  if [ -d "app/modules/${m}" ]; then
    log_ok "Module directory exists: ${m}"
  else
    log_warn "Missing module directory: ${m}"
  fi
done

# -------------------------------------------------
# 3. Check Python syntax
# -------------------------------------------------
echo ""
echo "=== 3. Checking Python syntax ==="

if command -v python >/dev/null 2>&1; then
  PYTHON=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  log_error "Python not found, skipping Python syntax checks"
  PYTHON=""
fi

if [ -n "${PYTHON}" ]; then
  while IFS= read -r -d '' file; do
    if "${PYTHON}" -m py_compile "${file}" >/dev/null 2>&1; then
      log_ok "Python syntax OK: ${file}"
    else
      log_error "Python syntax error: ${file}"
    fi
  done < <(find app -type f -name "*.py" -print0)
else
  log_warn "Skipping Python syntax validation"
fi

# -------------------------------------------------
# 4. Check TypeScript / Next.js syntax (basic)
# -------------------------------------------------
echo ""
echo "=== 4. Checking TypeScript / Next.js project ==="

if [ -f "apps/web/package.json" ]; then
  log_ok "Frontend package.json exists"
else
  log_warn "Missing apps/web/package.json"
fi

if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  if [ -f "apps/web/package.json" ]; then
    cd apps/web
    if npm run typecheck >/dev/null 2>&1; then
      log_ok "Frontend typecheck passed"
    else
      log_warn "Frontend typecheck failed or not configured"
    fi
    cd "${PROJECT_DIR}"
  fi
else
  log_warn "Node/npm not found, skipping TypeScript checks"
fi

# -------------------------------------------------
# 5. Check YAML syntax (docker-compose, prometheus, alertmanager)
# -------------------------------------------------
echo ""
echo "=== 5. Checking YAML syntax ==="

check_yaml() {
  local file="$1"
  if [ ! -f "${file}" ]; then
    log_warn "YAML file missing: ${file}"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PY=python
  elif command -v python3 >/dev/null 2>&1; then
    PY=python3
  else
    log_warn "Python not found, skipping YAML check for ${file}"
    return
  fi

  if "${PY}" -c "import yaml; yaml.safe_load(open('${file}'))" >/dev/null 2>&1; then
    log_ok "YAML syntax OK: ${file}"
  else
    log_error "YAML syntax error: ${file}"
  fi
}

check_yaml "docker-compose.yml"
check_yaml "docker-compose.monitoring.yml"
check_yaml "infra/prometheus/prometheus.yml"
check_yaml "infra/alertmanager/alertmanager.yml"
check_yaml "infra/loki/loki-config.yml"
check_yaml "infra/loki/promtail-config.yml"

# -------------------------------------------------
# 6. Check JSON syntax (Grafana dashboards)
# -------------------------------------------------
echo ""
echo "=== 6. Checking JSON syntax (Grafana dashboards) ==="

check_json() {
  local file="$1"
  if [ ! -f "${file}" ]; then
    log_warn "JSON file missing: ${file}"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    PY=python
  elif command -v python3 >/dev/null 2>&1; then
    PY=python3
  else
    log_warn "Python not found, skipping JSON check for ${file}"
    return
  fi

  if "${PY}" -c "import json; json.load(open('${file}'))" >/dev/null 2>&1; then
    log_ok "JSON syntax OK: ${file}"
  else
    log_error "JSON syntax error: ${file}"
  fi
}

for f in infra/grafana/dashboards/*.json; do
  [ -f "${f}" ] && check_json "${f}"
done

# -------------------------------------------------
# 7. Check Nginx config syntax
# -------------------------------------------------
echo ""
echo "=== 7. Checking Nginx configuration syntax ==="

if command -v nginx >/dev/null 2>&1; then
  if [ -f "infra/nginx/nginx.conf" ]; then
    if nginx -t -c "${PROJECT_DIR}/infra/nginx/nginx.conf" >/dev/null 2>&1; then
      log_ok "Nginx config syntax OK"
    else
      log_error "Nginx config syntax error"
    fi
  else
    log_warn "infra/nginx/nginx.conf missing"
  fi
else
  log_warn "nginx binary not found, skipping Nginx syntax check"
fi

# -------------------------------------------------
# 8. Check Docker Compose consistency
# -------------------------------------------------
echo ""
echo "=== 8. Checking Docker Compose consistency ==="

if command -v docker >/dev/null 2>&1 && command -v docker compose >/dev/null 2>&1; then
  if [ -f "docker-compose.yml" ]; then
    if docker compose config >/dev/null 2>&1; then
      log_ok "docker-compose.yml is valid"
    else
      log_error "docker-compose.yml validation failed"
    fi
  fi

  if [ -f "docker-compose.monitoring.yml" ]; then
    if docker compose -f docker-compose.monitoring.yml config >/dev/null 2>&1; then
      log_ok "docker-compose.monitoring.yml is valid"
    else
      log_error "docker-compose.monitoring.yml validation failed"
    fi
  fi
else
  log_warn "Docker Compose not available, skipping compose validation"
fi

# -------------------------------------------------
# 9. Check .env.production keys
# -------------------------------------------------
echo ""
echo "=== 9. Checking .env.production consistency ==="

ENV_FILE=".env.production"
if [ -f "${ENV_FILE}" ]; then
  REQUIRED_KEYS=(
    "APP_ENV"
    "APP_DOMAIN"
    "API_DOMAIN"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "DATABASE_URL"
    "REDIS_HOST"
    "MINIO_ROOT_USER"
    "MINIO_ROOT_PASSWORD"
    "S3_ENDPOINT_URL"
    "JWT_SECRET_KEY"
    "JWT_REFRESH_SECRET_KEY"
    "CORS_ALLOWED_ORIGINS"
    "NEXT_PUBLIC_API_BASE_URL"
  )

  for key in "${REQUIRED_KEYS[@]}"; do
    if grep -q "^${key}=" "${ENV_FILE}"; then
      log_ok "Env key present: ${key}"
    else
      log_warn "Missing env key: ${key}"
    fi
  done
else
  log_error ".env.production missing"
fi

# -------------------------------------------------
# 10. Check cross-module references (basic)
# -------------------------------------------------
echo ""
echo "=== 10. Checking basic cross-module references ==="

if grep -q "from app.shared.presentation.health_router import router as health_router" app/main.py; then
  log_ok "main.py imports health_router"
else
  log_warn "main.py may not import health_router correctly"
fi

if grep -q "from app.shared.presentation.metrics_router import router as metrics_router" app/main.py; then
  log_ok "main.py imports metrics_router"
else
  log_warn "main.py may not import metrics_router correctly"
fi

if grep -q "from app.shared.presentation.api_router import api_router" app/main.py; then
  log_ok "main.py imports api_router"
else
  log_warn "main.py may not import api_router correctly"
fi

if [ -f "app/shared/presentation/health_router.py" ]; then
  if grep -q 'router = APIRouter' app/shared/presentation/health_router.py; then
    log_ok "health_router defines APIRouter"
  else
    log_warn "health_router may not define APIRouter correctly"
  fi
else
  log_error "app/shared/presentation/health_router.py missing"
fi

if [ -f "app/shared/presentation/metrics_router.py" ]; then
  if grep -q 'router = APIRouter' app/shared/presentation/metrics_router.py; then
    log_ok "metrics_router defines APIRouter"
  else
    log_warn "metrics_router may not define APIRouter correctly"
  fi
else
  log_error "app/shared/presentation/metrics_router.py missing"
fi

# -------------------------------------------------
# 11. Check docs presence
# -------------------------------------------------
echo ""
echo "=== 11. Checking documentation files ==="

DOCS=(
  "docs/product-specification.md"
  "docs/deployment.md"
  "docs/finalization.md"
  "docs/monitoring.md"
  "docs/load-testing.md"
  "docs/architecture-overview.md"
  "docs/troubleshooting.md"
  "docs/production-readiness.md"
)

for d in "${DOCS[@]}"; do
  if [ -f "${d}" ]; then
    log_ok "Doc file exists: ${d}"
  else
    log_warn "Missing doc file: ${d}"
  fi
done

# -------------------------------------------------
# 12. Check scripts presence and executability
# -------------------------------------------------
echo ""
echo "=== 12. Checking scripts ==="

SCRIPTS=(
  "scripts/deploy.sh"
  "scripts/bootstrap-letsencrypt.sh"
  "scripts/backup.sh"
  "scripts/restore.sh"
  "scripts/health-check.sh"
  "scripts/logs.sh"
  "scripts/load-test.sh"
)

for s in "${SCRIPTS[@]}"; do
  if [ -f "${s}" ]; then
    log_ok "Script exists: ${s}"
    if [ -x "${s}" ]; then
      log_ok "Script is executable: ${s}"
    else
      log_warn "Script not executable: ${s}"
    fi
  else
    log_warn "Missing script: ${s}"
  fi
done

# -------------------------------------------------
# Summary
# -------------------------------------------------
echo ""
echo "=== Validation Summary ==="
echo "Errors: ${ERRORS}"
echo "Warnings: ${WARNINGS}"

if [ "${ERRORS}" -gt 0 ]; then
  echo "Validation FAILED with errors."
  exit 1
else
  echo "Validation PASSED (warnings may still exist)."
  exit 0
fi
