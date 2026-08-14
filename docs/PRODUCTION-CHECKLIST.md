# CMEP – produkčný checklist

1. APP_ENV=production, DEBUG=false
2. Silné JWT_SECRET_KEY a JWT_REFRESH_SECRET_KEY (nie auto-generované)
3. Silné POSTGRES_PASSWORD, zálohy DB
4. CORS len na reálnu doménu
5. HTTPS (reverse proxy: Caddy/Nginx)
6. Redis ak queue/cache
7. Nespoliehať sa na --reload v produkcii
8. Monitoring: /health, logy
9. Overené firmy pred publish (fáza C)
10. Audit + notifikácie (C2/C3)
