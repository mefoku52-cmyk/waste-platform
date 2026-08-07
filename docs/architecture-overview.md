# Architecture Overview

## Runtime

The platform consists of a FastAPI backend, a Next.js frontend, PostgreSQL, Redis and MinIO-compatible object storage.

## Backend

Backend source code is located in `app/`.

- `app/main.py` is the FastAPI application entry point.
- `app/modules/` contains business modules.
- `app/shared/domain/` contains shared domain primitives.
- `app/shared/application/` contains shared application services.
- `app/shared/infrastructure/` contains database, security and infrastructure adapters.
- `app/shared/presentation/` contains routers, schemas, middleware and exception handlers.

## Frontend

The Next.js application is located in `apps/web/`.

## Infrastructure

- `docker-compose.yml` defines the application runtime.
- `docker-compose.monitoring.yml` defines observability services.
- `infra/prometheus/` contains Prometheus configuration.
- `infra/loki/` contains Loki and Promtail configuration.
- `infra/alertmanager/` contains Alertmanager configuration.
- `scripts/` contains operational scripts.

## Health and metrics

The API exposes:

- `GET /health`
- `GET /metrics`

The metrics endpoint is intended for Prometheus scraping.

## Validation

Run Python syntax validation with:

```bash
python3 -m compileall -q app
docker compose --env-file .env.production -f docker-compose.yml config
docker compose --env-file .env.production -f docker-compose.monitoring.yml config

## 8. Oprava bezpečnosti `.env`

V súbore:

```text
/data/data/com.termux/files/home/waste-platform/.env
cd /data/data/com.termux/files/home/waste-platform

sed -n '1,120p' .env
chmod 600 .env .env.production
grep -nE '(^|/).env($|.production$)' .gitignore 2>/dev/null || true
/data/data/com.termux/files/home/waste-platform/.gitignore
cat << 'EOF' >> .gitignore

.env
.env.production
__pycache__/
*.pyc
node_modules/
.next/
infra/ssl/live/
infra/ssl/archive/
