#!/data/data/com.termux/files/usr/bin/bash
set -eu

echo '===== WHO USES 8010 ====='
ss -ltnp 2>/dev/null | grep ':8010 ' || true
echo

echo '===== HEALTH 8010 ====='
curl -i -m 10 http://localhost:8010/health || true
echo

echo '===== LOGIN 8010 ====='
curl -i -m 10 -X POST http://localhost:8010/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"nonexistent@example.com","password":"wrongpass"}' || true
echo

echo '===== IF 8010 IS BAD, START 8011 ====='
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 > "$HOME/cmep-backend-8011.log" 2>&1 &
sleep 4
tail -n 120 "$HOME/cmep-backend-8011.log" || true
echo

echo '===== HEALTH 8011 ====='
curl -i -m 10 http://localhost:8011/health || true
echo

echo '===== LOGIN 8011 ====='
curl -i -m 10 -X POST http://localhost:8011/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"nonexistent@example.com","password":"wrongpass"}' || true
echo

echo '===== LOG 8011 ====='
tail -n 120 "$HOME/cmep-backend-8011.log" || true
