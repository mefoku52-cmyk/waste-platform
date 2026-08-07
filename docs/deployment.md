# ============================================
# FILE: docker-compose.yml
# ============================================
version: "3.9"

name: cmep-platform-prod

services:
  nginx:
    image: nginx:1.27-alpine
    container_name: cmep-nginx
    restart: unless-stopped
    depends_on:
      web:
        condition: service_started
      api:
        condition: service_started
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./infra/ssl:/etc/letsencrypt
      - ./infra/certbot/www:/var/www/certbot
      - nginx_logs:/var/log/nginx
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1/ || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks:
      - cmep-network

  certbot:
    image: certbot/certbot:latest
    container_name: cmep-certbot
    restart: unless-stopped
    volumes:
      - ./infra/ssl:/etc/letsencrypt
      - ./infra/certbot/www:/var/www/certbot
    entrypoint: /bin/sh -c
    command: >
      "trap exit TERM;
      while :; do
        certbot renew --webroot -w /var/www/certbot --quiet;
        sleep 12h & wait $${!};
      done"
    networks:
      - cmep-network

  postgres:
    image: postgres:16
    container_name: cmep-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 15s
      timeout: 5s
      retries: 10
    networks:
      - cmep-network

  redis:
    image: redis:7-alpine
    container_name: cmep-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 15s
      timeout: 3s
      retries: 10
    networks:
      - cmep-network

  minio:
    image: minio/minio:latest
    container_name: cmep-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "-", "http://127.0.0.1:9000/minio/health/live"]
      interval: 15s
      timeout: 5s
      retries: 10
    networks:
      - cmep-network

  api:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: cmep-api
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      APP_ENV: production
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      REDIS_HOST: redis
      REDIS_PORT: 6379
      S3_ENDPOINT_URL: http://minio:9000
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    expose:
      - "8000"
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O - http://127.0.0.1:8000/health | grep -q 'ok'"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks:
      - cmep-network

  worker:
    build:
      context: ./app
      dockerfile: worker/Dockerfile
    container_name: cmep-worker
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      APP_ENV: production
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      REDIS_HOST: redis
      REDIS_PORT: 6379
      S3_ENDPOINT_URL: http://minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - cmep-network

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: cmep-web
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      NODE_ENV: production
      PORT: 3001
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL}
    depends_on:
      api:
        condition: service_healthy
    expose:
      - "3001"
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:3001/ || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks:
      - cmep-network

volumes:
  postgres_data:
  redis_data:
  minio_data:
  nginx_logs:

networks:
  cmep-network:
    driver: bridge

# ============================================
# FILE: infra/nginx/nginx.conf
# ============================================
user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
  worker_connections 1024;
}

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  log_format main '$remote_addr - $remote_user [$time_local] '
                  '"$request" $status $body_bytes_sent '
                  '"$http_referer" "$http_user_agent" '
                  'rt=$request_time ua="$upstream_addr" us="$upstream_status" urt="$upstream_response_time"';

  access_log /var/log/nginx/access.log main;

  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;
  keepalive_timeout 65;
  server_tokens off;
  types_hash_max_size 4096;
  client_max_body_size 50m;

  gzip on;
  gzip_comp_level 5;
  gzip_min_length 1024;
  gzip_proxied any;
  gzip_types
    text/plain
    text/css
    application/json
    application/javascript
    text/xml
    application/xml
    application/xml+rss
    text/javascript
    image/svg+xml;

  include /etc/nginx/conf.d/*.conf;
}

# ============================================
# FILE: infra/nginx/conf.d/default.conf.template
# ============================================
upstream cmep_frontend {
  server ;
}

upstream cmep_backend {
  server api:8000;
}

server {
  listen 80;
  listen [::]:80;
  server_name ${APP_DOMAIN} ${API_DOMAIN};

  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }

  location /healthz {
    return 200 'ok';
    add_header Content-Type text/plain;
  }

  location / {
    return 301 https://$host$request_uri;
  }
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name ${APP_DOMAIN};

  ssl_certificate /etc/letsencrypt/live/${APP_DOMAIN}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${APP_DOMAIN}/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers off;
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:10m;
  ssl_session_tickets off;

  add_header X-Frame-Options SAMEORIGIN always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  add_header X-XSS-Protection "1; mode=block" always;

  location / {
    proxy_pass http://cmep_frontend;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 60s;
  }
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name ${API_DOMAIN};

  ssl_certificate /etc/letsencrypt/live/${API_DOMAIN}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${API_DOMAIN}/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers off;
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:10m;
  ssl_session_tickets off;

  add_header X-Frame-Options SAMEORIGIN always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;
  add_header X-XSS-Protection "1; mode=block" always;

  location /healthz {
    return 200 'ok';
    add_header Content-Type text/plain;
  }

  location / {
    proxy_pass http://cmep_backend;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 60s;
  }
}

# ============================================
# FILE: infra/ssl/.gitkeep
# ============================================

# ============================================
# FILE: infra/certbot/www/.gitkeep
# ============================================

# ============================================
# FILE: scripts/deploy.sh
# ============================================
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
NGINX_TEMPLATE="${NGINX_TEMPLATE:-infra/nginx/conf.d/default.conf.template}"
NGINX_OUTPUT="${NGINX_OUTPUT:-infra/nginx/conf.d/default.conf}"

echo "[deploy] project dir: ${PROJECT_DIR}"
echo "[deploy] branch: ${BRANCH}"

if [ ! -d "${PROJECT_DIR}" ]; then
  echo "[deploy] missing project directory ${PROJECT_DIR}"
  exit 1
fi

cd "${PROJECT_DIR}"

mkdir -p infra/ssl infra/certbot/www infra/nginx/conf.d

if [ ! -f "${ENV_FILE}" ]; then
  echo "[deploy] missing ${ENV_FILE}"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

if [ -f "${NGINX_TEMPLATE}" ]; then
  envsubst '${APP_DOMAIN} ${API_DOMAIN}' < "${NGINX_TEMPLATE}" > "${NGINX_OUTPUT}"
fi

echo "[deploy] validating compose"
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config >/dev/null

echo "[deploy] building and starting services"
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build --remove-orphans

echo "[deploy] waiting for backend health"
ATTEMPTS=30
SLEEP_SECONDS=5
for ((i=1; i<=ATTEMPTS; i++)); do
  if docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T api wget -q -O - http://127.0.0.1:8000/health | grep -q "ok"; then
    echo "[deploy] backend health check passed"
    break
  fi
  echo "[deploy] health attempt ${i}/${ATTEMPTS} failed"
  sleep "${SLEEP_SECONDS}"
  if [ "${i}" -eq "${ATTEMPTS}" ]; then
    echo "[deploy] backend failed health check"
    docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" logs --tail=200 api
    exit 1
  fi
done

echo "[deploy] deployment completed"

# ============================================
# FILE: scripts/bootstrap-letsencrypt.sh
# ============================================
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/cmep-platform}"
ENV_FILE="${ENV_FILE:-.env.production}"

cd "${PROJECT_DIR}"

set -a
source "${ENV_FILE}"
set +a

if [ -z "${APP_DOMAIN:-}" ] || [ -z "${API_DOMAIN:-}" ] || [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
  echo "APP_DOMAIN, API_DOMAIN and LETSENCRYPT_EMAIL are required in ${ENV_FILE}"
  exit 1
fi

mkdir -p infra/ssl infra/certbot/www infra/nginx/conf.d

envsubst '${APP_DOMAIN} ${API_DOMAIN}' < infra/nginx/conf.d/default.conf.template > infra/nginx/conf.d/default.conf

docker compose --env-file "${ENV_FILE}" up -d nginx

docker compose --env-file "${ENV_FILE}" run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d "${APP_DOMAIN}" \
  -d "${API_DOMAIN}" \
  --email "${LETSENCRYPT_EMAIL}" \
  --agree-tos \
  --no-eff-email

docker compose --env-file "${ENV_FILE}" restart nginx

echo "Let's Encrypt certificates issued and nginx restarted."

# ============================================
# FILE: .github/workflows/deploy.yml
# ============================================
name: deploy

on:
  push:
    branches: ["main"]
  workflow_dispatch:

jobs:
  test-and-build:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: cmep_test
          POSTGRES_USER: cmep
          POSTGRES_PASSWORD: cmep
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U cmep -d cmep_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 10

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 10

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: apps/web/package-lock.json

      - name: Install backend dependencies
        working-directory: app
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx ruff

      - name: Lint backend
        working-directory: app
        run: |
          python -m ruff check .

      - name: Run backend tests
        working-directory: app
        env:
          APP_ENV: test
          DATABASE_URL: postgresql+asyncpg://cmep:cmep@127.0.0.1:5432/cmep_test
          DATABASE_HOST: 127.0.0.1
          DATABASE_PORT: 5432
          DATABASE_NAME: cmep_test
          DATABASE_USER: cmep
          DATABASE_PASSWORD: cmep
          REDIS_URL: redis://127.0.0.1:6379/0
          REDIS_HOST: 127.0.0.1
          REDIS_PORT: 6379
          JWT_SECRET_KEY: test-secret-key
          JWT_REFRESH_SECRET_KEY: test-refresh-secret-key
          JWT_ALGORITHM: HS256
          JWT_ACCESS_TOKEN_EXPIRES_MINUTES: 15
          JWT_REFRESH_TOKEN_EXPIRES_DAYS: 30
        run: |
          pytest

      - name: Install frontend dependencies
        working-directory: apps/web
        run: |
          if [ -f package-lock.json ]; then npm ci; else npm install; fi

      - name: Run frontend tests
        working-directory: apps/web
        run: |
          npm run test

      - name: Run frontend typecheck
        working-directory: apps/web
        run: |
          npm run typecheck

      - name: Build backend image
        run: |
          docker build -t cmep-api:${{ github.sha }} -f app/Dockerfile app

      - name: Build worker image
        run: |
          docker build -t cmep-worker:${{ github.sha }} -f app/worker/Dockerfile app

      - name: Build frontend image
        run: |
          docker build -t cmep-web:${{ github.sha }} -f apps/web/Dockerfile apps/web

  deploy:
    runs-on: ubuntu-latest
    needs: test-and-build

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Create production env file
        run: |
          cat > .env.production <<EOF
          APP_ENV=production
          APP_NAME=${{ secrets.APP_NAME }}
          APP_DOMAIN=${{ secrets.APP_DOMAIN }}
          API_DOMAIN=${{ secrets.API_DOMAIN }}
          LETSENCRYPT_EMAIL=${{ secrets.LETSENCRYPT_EMAIL }}
          APP_HOST=0.0.0.0
          APP_PORT=8000
          APP_DEBUG=false
          APP_LOG_LEVEL=INFO
          POSTGRES_DB=${{ secrets.POSTGRES_DB }}
          POSTGRES_USER=${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }}
          DATABASE_HOST=postgres
          DATABASE_PORT=5432
          DATABASE_NAME=${{ secrets.POSTGRES_DB }}
          DATABASE_USER=${{ secrets.POSTGRES_USER }}
          DATABASE_PASSWORD=${{ secrets.POSTGRES_PASSWORD }}
          DATABASE_URL=${{ secrets.DATABASE_URL }}
          REDIS_HOST=redis
          REDIS_PORT=6379
          REDIS_URL=${{ secrets.REDIS_URL }}
          MINIO_ROOT_USER=${{ secrets.MINIO_ROOT_USER }}
          MINIO_ROOT_PASSWORD=${{ secrets.MINIO_ROOT_PASSWORD }}
          S3_ENDPOINT_URL=http://minio:9000
          S3_PUBLIC_ENDPOINT_URL=${{ secrets.S3_PUBLIC_ENDPOINT_URL }}
          S3_REGION=${{ secrets.S3_REGION }}
          S3_ACCESS_KEY=${{ secrets.MINIO_ROOT_USER }}
          S3_SECRET_KEY=${{ secrets.MINIO_ROOT_PASSWORD }}
          S3_BUCKET_DOCUMENTS=${{ secrets.S3_BUCKET_DOCUMENTS }}
          S3_BUCKET_MEDIA=${{ secrets.S3_BUCKET_MEDIA }}
          S3_USE_SSL=false
          S3_FORCE_PATH_STYLE=true
          JWT_ISSUER=${{ secrets.JWT_ISSUER }}
          JWT_AUDIENCE=${{ secrets.JWT_AUDIENCE }}
          JWT_SECRET_KEY=${{ secrets.JWT_SECRET_KEY }}
          JWT_REFRESH_SECRET_KEY=${{ secrets.JWT_REFRESH_SECRET_KEY }}
          JWT_ACCESS_TOKEN_EXPIRES_MINUTES=${{ secrets.JWT_ACCESS_TOKEN_EXPIRES_MINUTES }}
          JWT_REFRESH_TOKEN_EXPIRES_DAYS=${{ secrets.JWT_REFRESH_TOKEN_EXPIRES_DAYS }}
          JWT_ALGORITHM=${{ secrets.JWT_ALGORITHM }}
          PASSWORD_BCRYPT_ROUNDS=12
          CORS_ALLOWED_ORIGINS=${{ secrets.CORS_ALLOWED_ORIGINS }}
          NEXT_PUBLIC_API_BASE_URL=${{ secrets.NEXT_PUBLIC_API_BASE_URL }}
          EMAIL_PROVIDER=${{ secrets.EMAIL_PROVIDER }}
          EMAIL_FROM=${{ secrets.EMAIL_FROM }}
          SMTP_HOST=${{ secrets.SMTP_HOST }}
          SMTP_PORT=${{ secrets.SMTP_PORT }}
          SMTP_USERNAME=${{ secrets.SMTP_USERNAME }}
          SMTP_PASSWORD=${{ secrets.SMTP_PASSWORD }}
          SMTP_USE_TLS=${{ secrets.SMTP_USE_TLS }}
          QUEUE_DRIVER=redis
          WORKER_CONCURRENCY=${{ secrets.WORKER_CONCURRENCY }}
          DEFAULT_PAGE_SIZE=20
          MAX_PAGE_SIZE=100
          OTEL_ENABLED=false
          SENTRY_DSN=${{ secrets.SENTRY_DSN }}
          REQUEST_ID_HEADER=X-Request-ID
          EOF

      - name: Copy project to VPS
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          port: ${{ secrets.DEPLOY_PORT }}
          source: "."
          target: "${{ secrets.DEPLOY_PATH }}"
          rm: false
          overwrite: true
          strip_components: 0

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          port: ${{ secrets.DEPLOY_PORT }}
          script: |
            cd "${{ secrets.DEPLOY_PATH }}"
            chmod +x scripts/deploy.sh scripts/bootstrap-letsencrypt.sh
            if [ ! -f "infra/ssl/live/${{ secrets.APP_DOMAIN }}/fullchain.pem" ]; then
              PROJECT_DIR="${{ secrets.DEPLOY_PATH }}" ENV_FILE=".env.production" ./scripts/bootstrap-letsencrypt.sh
            fi
            PROJECT_DIR="${{ secrets.DEPLOY_PATH }}" BRANCH="main" ENV_FILE=".env.production" ./scripts/deploy.sh

      - name: Verify API health
        run: |
          curl -fsSL "https://${{ secrets.API_DOMAIN }}/health" >/dev/null

# ============================================
# FILE: .env.production
# ============================================
APP_ENV=production
APP_NAME=Circular Materials Exchange Platform

APP_DOMAIN=app.example.com
API_DOMAIN=api.example.com
LETSENCRYPT_EMAIL=admin@example.com

APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
APP_LOG_LEVEL=INFO

POSTGRES_DB=cmep
POSTGRES_USER=cmep
POSTGRES_PASSWORD=change-me-postgres-password
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=cmep
DATABASE_USER=cmep
DATABASE_PASSWORD=change-me-postgres-password
DATABASE_URL=postgresql+asyncpg://cmep:change-me-postgres-password@postgres:5432/cmep

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=change-me-minio-password
S3_ENDPOINT_URL=http://minio:9000
S3_PUBLIC_ENDPOINT_URL=https://minio.example.com
S3_REGION=eu-central-1
S3_ACCESS_KEY=minio
S3_SECRET_KEY=change-me-minio-password
S3_BUCKET_DOCUMENTS=cmep-documents
S3_BUCKET_MEDIA=cmep-media
S3_USE_SSL=false
S3_FORCE_PATH_STYLE=true

JWT_ISSUER=cmep-api
JWT_AUDIENCE=cmep-web
JWT_SECRET_KEY=change-me-jwt-secret
JWT_REFRESH_SECRET_KEY=change-me-jwt-refresh-secret
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_ALGORITHM=HS256

PASSWORD_BCRYPT_ROUNDS=12

CORS_ALLOWED_ORIGINS=https://app.example.com
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1

EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=smtp-user
SMTP_PASSWORD=change-me-smtp-password
SMTP_USE_TLS=true

QUEUE_DRIVER=redis
WORKER_CONCURRENCY=2

DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

OTEL_ENABLED=false
SENTRY_DSN=
REQUEST_ID_HEADER=X-Request-ID

# ============================================
# FILE: app/shared/presentation/health_router.py
# ============================================
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def healthcheck():
    return {"status": "ok"}

# ============================================
# FILE: app/main.py
# ============================================
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.presentation.api_router import api_router
from app.shared.presentation.exception_handlers import register_exception_handlers
from app.shared.presentation.health_router import router as health_router

logging.basicConfig(
    level=getattr(logging, os.getenv("APP_LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Circular Materials Exchange Platform API",
    version="0.1.0",
)

cors_origins = [item.strip() for item in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(api_router)

# ============================================
# FILE: infra/ssl/README.md
# ============================================
This directory stores Let's Encrypt certificates and runtime certificate files.

Expected structure after initial issuance:
- infra/ssl/live/<domain>/fullchain.pem
- infra/ssl/live/<domain>/privkey.pem

Bootstrap flow:
1. Point APP_DOMAIN and API_DOMAIN DNS records to the VPS.
2. Fill .env.production with real secrets.
3. Run scripts/bootstrap-letsencrypt.sh on the VPS.
4. Run scripts/deploy.sh.
5. Keep the certbot container running for renewals.

# ============================================
# FILE: docs/vps-deploy-checklist.txt
# ============================================
1. Provision Ubuntu or Debian VPS with Docker Engine and Docker Compose plugin installed.
2. Open firewall ports 22, 80, 443, 9000, 9001 according to your exposure policy.
3. Create a deployment user with SSH key authentication only.
4. Clone or upload the repository to /opt/cmep-platform.
5. Fill .env.production with real secrets.
6. Ensure APP_DOMAIN and API_DOMAIN point to the VPS public IP.
7. Run scripts/bootstrap-letsencrypt.sh once.
8. Run scripts/deploy.sh.
9. Validate:
   - https://APP_DOMAIN
   - https://API_DOMAIN/health
   - docker compose ps
   - docker compose logs -f nginx api web worker
10. Set GitHub repository secrets for DEPLOY_HOST, DEPLOY_USER, DEPLOY_PORT, DEPLOY_SSH_KEY, DEPLOY_PATH and all application secrets.
