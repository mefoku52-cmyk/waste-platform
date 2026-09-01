#!/data/data/com.termux/files/usr/bin/bash
set -u

export PGPASSWORD='recyclehub'

echo '===== DATABASE CONNECTION ====='
psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U recyclehub \
  -d recyclehub \
  -c 'select current_database(), current_user, version();' || true
echo

echo '===== DATABASE TABLES ====='
psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U recyclehub \
  -d recyclehub \
  -c 'dt' || true
echo

echo '===== API HEALTH ====='
curl -i -m 10 http://localhost:8010/health || true
echo

echo '===== API LOGIN ====='
curl -i -m 10 -X POST http://localhost:8010/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"nonexistent@example.com","password":"wrongpass"}' || true
echo

echo '===== CLEAN BACKEND LOG ====='
tail -n 120 "$HOME/cmep-backend-clean.log" 2>/dev/null || true
