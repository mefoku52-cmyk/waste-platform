#!/bin/bash

echo "🔧 OPRAVA A SPUSTENIE APLIKÁCIE"
echo "========================================="

# 1. Choď do koreňa
cd ~/waste-platform
echo "📋 1. Adresár: $(pwd)"

# 2. Skontroluj alembic.ini
echo ""
echo "📋 2. Kontrola alembic.ini..."
if [ ! -f "alembic.ini" ]; then
    echo "⚠️  alembic.ini chýba, vytváram..."
    cat > alembic.ini << 'INIEOF'
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://recyclehub:recyclehub@127.0.0.1:5432/recyclehub

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = 

[formatters]
keys = 

[logger_root]
level = WARN
handlers = 
qualname =

[logger_sqlalchemy]
level = WARN
handlers = 
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers = 
qualname = alembic

[handler_root]
level = INFO
handlers = 

[handler_sqlalchemy]
level = WARN
handlers = 

[handler_alembic]
level = INFO
handlers = 
INIEOF
    echo "✅ alembic.ini vytvorený"
else
    echo "✅ alembic.ini existuje"
fi

# 3. Skontroluj Alembic
echo ""
echo "📋 3. Kontrola Alembic..."
alembic current 2>/dev/null || echo "⚠️  Alembic nie je inicializovaný"

# 4. Zabi staré procesy
echo ""
echo "📋 4. Zastavujem staré procesy..."
pkill -f uvicorn 2>/dev/null
sleep 2

# 5. Spusti aplikáciu
echo ""
echo "📋 5. Spúšťam aplikáciu..."
cd app
uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
sleep 5

# 6. Test
echo ""
echo "📋 6. Test API..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Aplikácia neodpovedá"

# 7. Zhrnutie
echo ""
echo "========================================="
echo "📊 ZHRNUTIE"
echo "========================================="
echo "✅ Aplikácia: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null)"
echo "✅ Alembic: $(alembic current 2>/dev/null | head -1 || echo 'N/A')"
echo "🔗 http://localhost:8000/docs"
echo "========================================="
