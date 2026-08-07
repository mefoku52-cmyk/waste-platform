# ============================================
# FILE: app/Dockerfile
# ============================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /srv/app

RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /srv/app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# FILE: app/worker/Dockerfile
# ============================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /srv/app

RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /srv/app
USER appuser

CMD ["python", "-m", "app.worker.main"]

# ============================================
# FILE: apps/web/Dockerfile
# ============================================
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules /app/node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3001

RUN addgroup -S nextjs && adduser -S nextjs -G nextjs

COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/public /app/public
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/node_modules /app/node_modules
COPY --from=builder /app/next.config.js /app/next.config.js

USER nextjs

EXPOSE 3001

CMD ["npm", "run", "start"]

# ============================================
# FILE: docker-compose.yml
# ============================================
version: "3.9"

name: cmep-platform

services:
  postgres:
    image: postgres:16
    container_name: cmep-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-cmep}
      POSTGRES_USER: ${POSTGRES_USER:-cmep}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cmep}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-cmep} -d ${POSTGRES_DB:-cmep}"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks:
      - cmep-network

  redis:
    image: redis:7-alpine
    container_name: cmep-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
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
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minio}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minio123}
    ports:
      - "${MINIO_API_PORT:-9000}:9000"
      - "${MINIO_CONSOLE_PORT:-9001}:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
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
      - .env
    environment:
      APP_ENV: ${APP_ENV:-development}
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      REDIS_HOST: redis
      REDIS_PORT: 6379
      S3_ENDPOINT_URL: http://minio:9000
      S3_REGION: ${S3_REGION:-eu-central-1}
      S3_ACCESS_KEY: ${MINIO_ROOT_USER:-minio}
      S3_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minio123}
      S3_BUCKET_DOCUMENTS: ${S3_BUCKET_DOCUMENTS:-cmep-documents}
      S3_BUCKET_MEDIA: ${S3_BUCKET_MEDIA:-cmep-media}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS:-http://localhost:3001}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    ports:
      - "${API_PORT:-8000}:8000"
    networks:
      - cmep-network

  worker:
    build:
      context: ./app
      dockerfile: worker/Dockerfile
    container_name: cmep-worker
    restart: unless-stopped
    env_file:
      - .env
    environment:
      APP_ENV: ${APP_ENV:-development}
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      REDIS_HOST: redis
      REDIS_PORT: 6379
      S3_ENDPOINT_URL: http://minio:9000
      S3_REGION: ${S3_REGION:-eu-central-1}
      S3_ACCESS_KEY: ${MINIO_ROOT_USER:-minio}
      S3_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-minio123}
      S3_BUCKET_DOCUMENTS: ${S3_BUCKET_DOCUMENTS:-cmep-documents}
      S3_BUCKET_MEDIA: ${S3_BUCKET_MEDIA:-cmep-media}
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
      args:
        NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000/api/v1}
    container_name: cmep-web
    restart: unless-stopped
    env_file:
      - .env
    environment:
      NODE_ENV: production
      PORT: 3001
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000/api/v1}
    depends_on:
      api:
        condition: service_started
    ports:
      - "${WEB_PORT:-3001}:3001"
    networks:
      - cmep-network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  cmep-network:
    driver: bridge

# ============================================
# FILE: .env.example
# ============================================
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_NAME=Circular Materials Exchange Platform
APP_DEBUG=true
APP_LOG_LEVEL=INFO

API_PORT=8000
WEB_PORT=3001
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

POSTGRES_DB=cmep
POSTGRES_USER=cmep
POSTGRES_PASSWORD=cmep
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=cmep
DATABASE_USER=cmep
DATABASE_PASSWORD=cmep
DATABASE_URL=postgresql+asyncpg://cmep:cmep@postgres:5432/cmep

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123

S3_ENDPOINT_URL=http://minio:9000
S3_PUBLIC_ENDPOINT_URL=http://localhost:9000
S3_REGION=eu-central-1
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123
S3_BUCKET_DOCUMENTS=cmep-documents
S3_BUCKET_MEDIA=cmep-media
S3_USE_SSL=false
S3_FORCE_PATH_STYLE=true

JWT_ISSUER=cmep-api
JWT_AUDIENCE=cmep-web
JWT_SECRET_KEY=change-me-super-secret-key
JWT_REFRESH_SECRET_KEY=change-me-super-secret-refresh-key
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_ALGORITHM=HS256

PASSWORD_BCRYPT_ROUNDS=12

CORS_ALLOWED_ORIGINS=http://localhost:3001
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,PATCH,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Authorization,Content-Type,X-Correlation-ID

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

EMAIL_PROVIDER=console
EMAIL_FROM=noreply@cmep.local
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true

QUEUE_DRIVER=redis
WORKER_CONCURRENCY=2

DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

OTEL_ENABLED=false
SENTRY_DSN=
REQUEST_ID_HEADER=X-Request-ID

# ============================================
# FILE: .github/workflows/ci.yml
# ============================================
name: ci

on:
  push:
    branches: ["main", "master", "develop"]
  pull_request:
    branches: ["*"]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app

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

    env:
      APP_ENV: test
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      DATABASE_HOST: 127.0.0.1
      DATABASE_PORT: 5432
      DATABASE_NAME: cmep_test
      DATABASE_USER: cmep
      DATABASE_PASSWORD: cmep
      DATABASE_URL: postgresql+asyncpg://cmep:cmep@127.0.0.1:5432/cmep_test
      REDIS_HOST: 127.0.0.1
      REDIS_PORT: 6379
      REDIS_URL: redis://127.0.0.1:6379/0
      JWT_SECRET_KEY: test-secret-key
      JWT_REFRESH_SECRET_KEY: test-refresh-secret-key
      JWT_ACCESS_TOKEN_EXPIRES_MINUTES: 15
      JWT_REFRESH_TOKEN_EXPIRES_DAYS: 30
      JWT_ALGORITHM: HS256
      S3_ENDPOINT_URL: http://127.0.0.1:9000
      S3_ACCESS_KEY: minio
      S3_SECRET_KEY: minio123
      S3_BUCKET_DOCUMENTS: cmep-documents
      S3_BUCKET_MEDIA: cmep-media

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx ruff

      - name: Lint backend
        run: |
          python -m ruff check .

      - name: Run backend tests
        run: |
          pytest

      - name: Build backend image
        run: |
          docker build -t cmep-api:${{ github.sha }} -f Dockerfile .

      - name: Build worker image
        run: |
          docker build -t cmep-worker:${{ github.sha }} -f worker/Dockerfile .

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web

    env:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000/api/v1

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: apps/web/package-lock.json

      - name: Install dependencies
        run: |
          if [ -f package-lock.json ]; then npm ci; else npm install; fi

      - name: Typecheck
        run: |
          npm run typecheck

      - name: Run frontend tests
        run: |
          npm run test

      - name: Build frontend
        run: |
          npm run build

      - name: Build frontend image
        run: |
          docker build -t cmep-web:${{ github.sha }} -f Dockerfile .

# ============================================
# FILE: Makefile
# ============================================
SHELL := /bin/bash

COMPOSE := docker compose
APP_DIR := app
WEB_DIR := apps/web

.PHONY: help dev api web test test-backend test-frontend lint lint-backend typecheck web-build build up down logs ps restart clean

help:
	@echo "Available commands:"
	@echo "  make dev            - start backend and frontend locally"
	@echo "  make api            - run FastAPI locally on :8000"
	@echo "  make web            - run Next.js locally on :3001"
	@echo "  make test           - run backend and frontend tests"
	@echo "  make test-backend   - run backend tests"
	@echo "  make test-frontend  - run frontend tests"
	@echo "  make lint           - run linting"
	@echo "  make lint-backend   - run backend lint"
	@echo "  make typecheck      - run frontend typecheck"
	@echo "  make build          - build all Docker images"
	@echo "  make up             - start docker compose stack"
	@echo "  make down           - stop docker compose stack"
	@echo "  make logs           - stream docker compose logs"
	@echo "  make ps             - list compose services"
	@echo "  make restart        - restart compose services"
	@echo "  make clean          - remove compose volumes"

dev:
	@echo "Run backend and frontend in separate terminals:"
	@echo "  make api"
	@echo "  make web"

api:
	cd $(APP_DIR) && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

web:
	cd $(WEB_DIR) && npm run dev

test: test-backend test-frontend

test-backend:
	cd $(APP_DIR) && pytest

test-frontend:
	cd $(WEB_DIR) && npm run test

lint: lint-backend typecheck

lint-backend:
	cd $(APP_DIR) && python -m ruff check .

typecheck:
	cd $(WEB_DIR) && npm run typecheck

web-build:
	cd $(WEB_DIR) && npm run build

build:
	$(COMPOSE) build

up:
	$(COMPOSE) --env-file .env up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) restart

clean:
	$(COMPOSE) down -v

# ============================================
# FILE: .dockerignore
# ============================================
.git
.gitignore
.github
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov
node_modules
.next
dist
build
.env
.env.*
docs
postgres_data
redis_data
minio_data

# ============================================
# FILE: apps/web/.dockerignore
# ============================================
node_modules
.next
coverage
dist
.env
.env.*
npm-debug.log

# ============================================
# FILE: app/.dockerignore
# ============================================
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov
.env
.env.*
tests
docs
