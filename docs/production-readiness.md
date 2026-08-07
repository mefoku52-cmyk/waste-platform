
Production Readiness Checklist

Security

☐ all default secrets replaced
☐ TLS enabled and certificates valid
☐ HSTS enabled
☐ CORS configured for real frontend origins only
☐ rate limiting enabled on public API
☐ firewall rules reviewed
☐ MinIO exposure reviewed

Reliability

☐ health endpoint enabled
☐ monitoring stack deployed
☐ alerts configured to a real receiver
☐ backups automated
☐ restore tested on a non-production environment
☐ deploy script tested twice

Observability

☐ /metrics exposed and scraped
☐ dashboards available in Grafana
☐ logs flowing to Loki
☐ request latency and error rates visible
  EOF
  echo "  ✅ docs/production-readiness.md"

echo ""

============================================

5. CHÝBAJÚCE SKRIPTY

============================================

echo "📄 5. VYTVÁRAM CHÝBAJÚCE SKRIPTY..."
echo "----------------------------------------"

scripts/deploy.sh

cat > scripts/deploy.sh << 'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

cd "${PROJECT_DIR}"
echo "[deploy] building and starting services"
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build --remove-orphans
echo "[deploy] deployment completed"
