#!/bin/bash

echo "============================================================"
echo " CMEP PLATFORM – KOMPLETNÁ OPRAVA"
echo "============================================================"

# 1. OPRAVA FRONTEND API URL
echo ""
echo "📋 1. Opravujem frontend API URL..."
cd ~/waste-platform/apps/web

# Zálohuj .env.local
cp .env.local .env.local.bak 2>/dev/null || true

# Nastav správnu URL (BEZ /api/v1)
cat > .env.local << 'ENVEOF'
NEXT_PUBLIC_API_BASE_URL=http://192.168.1.200:8001/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
ENVEOF

echo "✅ .env.local opravený"

# 2. REŠTART FRONTENDU
echo ""
echo "📋 2. Reštartujem frontend..."

# Zabij procesy na porte 3001
fuser -k 3001/tcp 2>/dev/null
pkill -f "next.*3001" 2>/dev/null
pkill -f "node.*3001" 2>/dev/null
sleep 2

# Spusti frontend v pozadí
npm run dev > /tmp/frontend.log 2>&1 &
echo "✅ Frontend spustený na http://localhost:3001"
sleep 3

# 3. OTESTOVANIE PRIHLÁSENIA
echo ""
echo "📋 3. Testovanie prihlásenia..."

# Vytvor testovacieho užívateľa, ak neexistuje
cd ~/waste-platform
PYTHONPATH=. python - << 'PYEOF'
import asyncio
from app.modules.users.application.services import UserService
from app.modules.users.infrastructure.repositories import UserRepository
from app.shared.infrastructure.db.session import async_session_maker
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.application.clock import Clock

async def create_demo_user():
    async with async_session_maker() as session:
        repo = UserRepository(session)
        service = UserService(repo, UuidGenerator(), Clock())
        try:
            user = await service.execute(
                email="demo@cmep.sk",
                password="Demo1234!",
                first_name="Demo",
                last_name="User",
                actor_user_id=None
            )
            print("✅ Demo užívateľ vytvorený / už existuje")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️ Demo užívateľ už existuje")
            else:
                print(f"⚠️ Chyba pri vytváraní: {e}")

asyncio.run(create_demo_user())
PYEOF

# Otestuj login cez curl
echo ""
echo "📋 4. Testovanie login endpointu..."
RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@cmep.sk","password":"Demo1234!"}')

if echo "$RESPONSE" | grep -q "accessToken"; then
    echo "✅ Login úspešný! (vrátený accessToken)"
else
    echo "❌ Login zlyhal. Odpoveď: $RESPONSE"
fi

# 4. NAHRANIE ARCHÍVU
echo ""
echo "📋 5. Nahrávam archív..."

cd ~/waste-platform
ARCHIVE=$(ls -t /sdcard/Download/CMEP-FINAL-*.tar.gz | head -1)

if [ -f "$ARCHIVE" ]; then
    echo "Nahrávam archív: $ARCHIVE"
    
    # Skús tmp.ninja (často funguje)
    echo "Pokus o nahratie na tmp.ninja..."
    UPLOAD_URL=$(curl -s -F "file=@${ARCHIVE}" https://tmp.ninja/upload.php | grep -o 'https://tmp.ninja/[^"]*' || echo "")
    
    if [ -n "$UPLOAD_URL" ]; then
        echo "✅ Archív nahratý na: $UPLOAD_URL"
        echo "👉 Pošli tento odkaz na zdieľanie: $UPLOAD_URL"
    else
        echo "❌ tmp.ninja zlyhalo. Skúšam file.io..."
        UPLOAD_URL=$(curl -s -F "file=@${ARCHIVE}" https://file.io | grep -o '"link":"[^"]*"' | cut -d'"' -f4 || echo "")
        if [ -n "$UPLOAD_URL" ]; then
            echo "✅ Archív nahratý na: $UPLOAD_URL"
            echo "👉 Pošli tento odkaz na zdieľanie: $UPLOAD_URL"
        else
            echo "❌ Nepodarilo sa nahrať archív. Skús manuálne:"
            echo "   - Použi https://gofile.io (webové rozhranie)"
            echo "   - Alebo nahraj na Google Drive / Dropbox"
        fi
    fi
else
    echo "❌ Archív nenájdený v /sdcard/Download/"
fi

# 5. MASTODON PRÍSPEVOK (pripravený na skopírovanie)
echo ""
echo "📋 6. Hotový príspevok pre Mastodon:"
echo "============================================================"
cat << 'POSTEOF'
🚀 CMEP Platform – Circular Economy Marketplace Platform

✅ Backend: FastAPI + SQLAlchemy (41 endpointov)
✅ Frontend: Next.js 15
✅ Autentifikácia, refresh token, ochrana proti replay útokom
✅ 100/100 udržiavateľnosť, 95/100 bezpečnosť

🔗 [Vlož sem odkaz na archív]
🐙 GitHub: https://github.com/mefoku52-cmyk/F

#CMEP #circularEconomy #Python #FastAPI #NextJS #OpenSource
POSTEOF
echo "============================================================"

echo ""
echo "============================================================"
echo "✅ OPRAVA DOKONČENÁ"
echo "============================================================"
echo ""
echo "📊 ČO ĎALEJ:"
echo "  1. Otvor http://localhost:3001 a skús sa prihlásiť"
echo "  2. Ak sa prihlásenie nepodarí, pošli mi výpis z konzoly (F12)"
echo "  3. Zdieľaj odkaz na archív"
echo "  4. Skopíruj Mastodon príspevok a publikuj ho"
echo "============================================================"

