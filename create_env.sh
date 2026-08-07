#!/data/data/com.termux/files/usr/bin/bash

# Vytvorenie .env súboru
cat > .env << 'ENV'
# Database
POSTGRES_USER=recyclehub
POSTGRES_PASSWORD=recyclehub
POSTGRES_DB=recyclehub
DATABASE_URL=postgresql://recyclehub:recyclehub@localhost:5432/recyclehub

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=supersecretkeyforrecyclehubplatform2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000/ws

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@recyclehub.sk

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# GDPR
GDPR_ENABLED=True
GDPR_COOKIE_CONSENT=True
ENV

echo ".env súbor vytvorený"
