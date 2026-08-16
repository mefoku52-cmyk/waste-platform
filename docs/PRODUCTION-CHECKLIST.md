# CMEP – Production checklist

## P0 stabilizácia (hotové 2026-08-16)

- [x] Git checkpoint + tag `checkpoint-pre-production-20260816`
- [x] Tar archív + DB backup (`\~/cmep-backups/`)
- [x] FRONTEND_URL v reset e-maile (`settings.frontend_url`)
- [x] resetToken len v development
- [x] JWT secrets regenerované (nie v gite)
- [x] SMTP Gmail App Password funguje (emailSent=true)
- [x] Rate limit login + forgot
- [x] Admin ACL (`PLATFORM_ADMIN_EMAILS`)
- [x] Smoke: health, login, companies, listings, marketplace

## P1 server (ďalej)

- [ ] VPS / cloud inštancia
- [ ] Docker Compose (api + web + postgres + redis)
- [ ] Doména + DNS
- [ ] Nginx reverse proxy
- [ ] HTTPS (Let's Encrypt)
- [ ] FRONTEND_URL=https://tvoja-domena
- [ ] CORS_ALLOWED_ORIGINS na produkčnú doménu

## P2 produkčné správanie

- [x] Swagger/OpenAPI vypnutý pri is_production

- [x] APP_ENV=production, DEBUG=false (env example + docs gated)
- [ ] Silné JWT / DB heslá len na serveri
- [x] Cron DB backup (scripts/backup/cron-example.txt)
- [ ] Log rotácia + /health monitoring
- [ ] Žiadne tajomstvá v gite

## P3 produkt

- [ ] Upload súborov (MinIO/S3)
- [ ] Admin UI oddelené
- [ ] E-mail šablóny
- [ ] GDPR / cookies texty
