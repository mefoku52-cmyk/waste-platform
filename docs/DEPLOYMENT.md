# CMEP – nasadenie na VPS (P1)

## Predpoklady
- Ubuntu 22.04+ VPS, verejná IP
- Doména → A record na IP (môže prísť neskôr)
- Docker + Docker Compose plugin

## Kroky
1. Nahraj projekt na server (git clone alebo scp)
2. cp .env.production.example .env.production a vyplň secrets
3. docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
4. Over: curl http://IP/health
5. HTTPS – až keď máš doménu (sekcia nižšie)
6. FRONTEND_URL a CORS na https://tvoja-domena

## Poznámky
- API vnútorne :8000; vonku nginx :80 / :443
- Web vnútorne :3001
- FE: NEXT_PUBLIC_API_BASE_URL + /api/v1/...
- Bez domény: dočasne http://IP (CORS a cookies treba doladiť)

## HTTPS (Let's Encrypt) – až s doménou
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tvoja-domena.sk

Po HTTPS v .env.production:
FRONTEND_URL=https://tvoja-domena.sk
CORS_ALLOWED_ORIGINS=["https://tvoja-domena.sk"]
NEXT_PUBLIC_API_BASE_URL=https://tvoja-domena.sk
# rebuild web image
