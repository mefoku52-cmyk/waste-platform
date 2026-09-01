#!/bin/bash

echo "📦 PRESÚVAM AUDIT VÝSLEDKY DO TELEFÓNU"
echo "========================================="

# 1. Zisti posledný audit
AUDIT_FILE=$(ls -t FINAL-AUTHORITY-AUDIT-*.txt 2>/dev/null | head -1)
if [ -z "$AUDIT_FILE" ]; then
    echo "❌ Žiadny auditný súbor nenájdený!"
    exit 1
fi

echo "📋 Auditný súbor: $AUDIT_FILE"

# 2. Skopíruj audit do Download
echo ""
echo "📋 Kopírujem audit do /sdcard/Download/..."
cp "$AUDIT_FILE" /sdcard/Download/
echo "✅ Audit skopírovaný"

# 3. Skopíruj aj ďalšie dôležité súbory
echo ""
echo "📋 Kopírujem ďalšie dôležité súbory..."
cp STEP-09-SCHEMA-PROVENANCE-AUDIT-*.txt /sdcard/Download/ 2>/dev/null || echo "ℹ️  Žiadny STEP-09 súbor"
cp .env /sdcard/Download/waste-platform.env 2>/dev/null || echo "ℹ️  Žiadny .env súbor"
cp alembic.ini /sdcard/Download/waste-platform-alembic.ini 2>/dev/null || echo "ℹ️  Žiadny alembic.ini"

# 4. Vytvor archív
echo ""
echo "📋 Vytváram archív..."
ARCHIVE_NAME="waste-platform-audit-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "/sdcard/Download/$ARCHIVE_NAME" \
    FINAL-AUTHORITY-AUDIT-*.txt \
    STEP-09-SCHEMA-PROVENANCE-AUDIT-*.txt \
    .env \
    alembic.ini \
    2>/dev/null

echo "✅ Archív vytvorený: /sdcard/Download/$ARCHIVE_NAME"

# 5. Zobraz výsledok
echo ""
echo "========================================="
echo "📊 VÝSLEDOK PRESUNU"
echo "========================================="
echo ""
echo "📁 Súbory v /sdcard/Download/:"
ls -lh /sdcard/Download/FINAL-AUTHORITY-AUDIT-*.txt 2>/dev/null
echo ""
ls -lh /sdcard/Download/waste-platform-audit-*.tar.gz 2>/dev/null
echo ""
echo "📊 VEĽKOSŤ ARCHÍVU:"
du -sh /sdcard/Download/waste-platform-audit-*.tar.gz 2>/dev/null
echo ""
echo "========================================="
echo "✅ HOTOVO!"
echo "========================================="
