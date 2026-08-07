
Monitoring and Logging

Components

· Prometheus for metrics scraping and alert rule evaluation
· Grafana for dashboards and exploration
· Loki for centralized log aggregation
· Promtail for collecting Docker and host logs
· Alertmanager for alert routing

Start the stack

```bash
docker compose --env-file .env.production -f docker-compose.monitoring.yml up -d
```

Metrics endpoints

· API metrics: http://api:8000/metrics
· Prometheus: http://localhost:9090
· Grafana: http://localhost:3000
· Loki: http://localhost:3100
  EOF
  echo "  ✅ docs/monitoring.md"

docs/architecture-overview.md

cat > docs/architecture-overview.md << 'EOF'

Architecture Overview

System context

The platform consists of:

· Next.js frontend for company users, admins and operators
· FastAPI backend as the application API
· PostgreSQL as the system of record
· Redis as cache and queue backend
· MinIO as S3-compatible document and media storage
· Nginx as reverse proxy and TLS termination
· Worker service for asynchronous background tasks
· Prometheus, Grafana, Loki, Promtail and Alertmanager for observability

Simplified architecture diagram

```
[ Browser ] -> [ Nginx :80/:443 ] -> [ Next.js Web :3001 ] -> [ FastAPI API :8000 ]
                                     [ FastAPI API :8000 ] -> [ PostgreSQL 16 ]
                                     [ FastAPI API :8000 ] -> [ Redis ]
                                     [ FastAPI API :8000 ] -> [ MinIO ]
                                     [ FastAPI API :8000 ] -> [ Worker ]
                                     [ FastAPI API :8000 ] -> [ /metrics ] -> [ Prometheus ]
```

