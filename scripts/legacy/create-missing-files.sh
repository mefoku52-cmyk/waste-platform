#!/bin/bash

echo "🛠️ VYTVÁRAM CHÝBAJÚCE SÚBORY..."

# 1. .env
cat > .env << 'ENVEOF'
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=postgresql+asyncpg://cmep:cmep@postgres:5432/cmep
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=change-me-super-secret-key
JWT_REFRESH_SECRET_KEY=change-me-super-secret-refresh-key
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENVEOF
echo "✅ .env vytvorený"

# 2. apps/web/.env.local
mkdir -p apps/web
cat > apps/web/.env.local << 'ENVEOF'
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENVEOF
echo "✅ apps/web/.env.local vytvorený"

# 3. docker-compose.monitoring.yml
cat > docker-compose.monitoring.yml << 'ENVEOF'
version: "3.9"
name: cmep-monitoring
services:
  prometheus:
    image: prom/prometheus:v2.54.1
    container_name: cmep-prometheus
    restart: unless-stopped
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=15d
    ports:
      - "9090:9090"
    volumes:
      - prometheus_data:/prometheus
    networks:
      - monitoring-network
  grafana:
    image: grafana/grafana:11.1.4
    container_name: cmep-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring-network
  loki:
    image: grafana/loki:3.1.1
    container_name: cmep-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/loki-config.yml
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    networks:
      - monitoring-network
volumes:
  prometheus_data:
  grafana_data:
  loki_data:
networks:
  monitoring-network:
    driver: bridge
ENVEOF
echo "✅ docker-compose.monitoring.yml vytvorený"

# 4. scripts/backup.sh
mkdir -p scripts
cat > scripts/backup.sh << 'ENVEOF'
#!/bin/bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_DIR}/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"
cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
echo "[backup] creating backup directory ${BACKUP_DIR}"
echo "[backup] backing up postgres"
docker compose --env-file "${ENV_FILE}" exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > "${BACKUP_DIR}/postgres.sql"
echo "[backup] done: ${BACKUP_DIR}"
ENVEOF
chmod +x scripts/backup.sh
echo "✅ scripts/backup.sh vytvorený"

# 5. scripts/restore.sh
cat > scripts/restore.sh << 'ENVEOF'
#!/bin/bash
set -Eeuo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi
BACKUP_DIR="$1"
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
if [ ! -d "${BACKUP_DIR}" ]; then
  echo "Backup directory not found: ${BACKUP_DIR}"
  exit 1
fi
cd "${PROJECT_DIR}"
set -a
source "${ENV_FILE}"
set +a
echo "[restore] restoring postgres"
cat "${BACKUP_DIR}/postgres.sql" | docker compose --env-file "${ENV_FILE}" exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
echo "[restore] done"
ENVEOF
chmod +x scripts/restore.sh
echo "✅ scripts/restore.sh vytvorený"

# 6. scripts/health-check.sh
cat > scripts/health-check.sh << 'ENVEOF'
#!/bin/bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"
cd "${PROJECT_DIR}"
echo "[health] docker compose ps"
docker compose --env-file "${ENV_FILE}" ps
echo "[health] api"
curl -fsSL "${API_HEALTH_URL:-https://api.example.com/health}" >/dev/null && echo "api ok" || echo "api failed"
echo "[health] frontend"
curl -fsSL "${APP_HEALTH_URL:-https://app.example.com}" >/dev/null && echo "frontend ok" || echo "frontend failed"
ENVEOF
chmod +x scripts/health-check.sh
echo "✅ scripts/health-check.sh vytvorený"

echo ""
echo "✅ VŠETKY CHÝBAJÚCE SÚBORY BOLI VYTVORENÉ!"
echo ""
echo "📁 KONTROLA:"
ls -la .env apps/web/.env.local docker-compose.monitoring.yml scripts/
