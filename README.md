# Circular Materials Exchange Platform (CMEP)

B2B platforma pre obchodovanie s odpadmi, vedľajšími produktmi a sekundárnymi surovinami.

## Rýchly štart
```bash
cp .env.example .env
docker compose up -d
```

Dokumentácia

· SUMMARY.md
· deployment.md
· monitoring.md
· load-testing.md

Technológie

· FastAPI + Python
· Next.js + TypeScript
· PostgreSQL, Redis, MinIO
· Docker, Prometheus, Grafana
  EOF
  echo "  ✅ README.md"

.env.production

cat > .env.production << 'EOF'
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
S3_REGION=eu-central-1
S3_ACCESS_KEY=minio
S3_SECRET_KEY=change-me-minio-password
S3_BUCKET_DOCUMENTS=cmep-documents
S3_BUCKET_MEDIA=cmep-media
JWT_ISSUER=cmep-api
JWT_AUDIENCE=cmep-web
JWT_SECRET_KEY=change-me-jwt-secret
JWT_REFRESH_SECRET_KEY=change-me-jwt-refresh-secret
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_ALGORITHM=HS256
CORS_ALLOWED_ORIGINS=https://app.example.com
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1
# waste-platform
