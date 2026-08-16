# CMEP – nasadenie na VPS (P1)

## Predpoklady
- Ubuntu 22.04+ VPS, verejná IP
- Doména → A record na IP
- Docker + Docker Compose plugin

## Kroky
1. `git clone` / nahraj projekt na server
2. `cp .env.production.example .env.production` a vyplň secrets
3. `docker compose -f docker-compose.production.yml --env-file .env.production up -d --build`
4. Over: `curl http://IP/health`
5. HTTPS: certbot (nginx plugin) alebo Caddy – doplníme v P1.2
6. Nastav `FRONTEND_URL` a `CORS_ALLOWED_ORIGINS` na `https://tvoja-domena`

## Poznámky
- API je vnútorné na porte 8000; vonku len nginx :80/:443
- Web Next.js na 3001 vnútorné
- Zálohy: `pg_dump` z kontajnera postgres
