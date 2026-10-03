#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# CMEP — Security Audit Script
# =============================================================================

set -Eeuo pipefail

ERRORS=0
WARNINGS=0

log_ok()   { echo "  ✅ $1"; }
log_warn() { echo "  ⚠️  $1"; ((WARNINGS++)); }
log_err()  { echo "  ❌ $1"; ((ERRORS++)); }

echo "=================================================================="
echo "🔐 CMEP SECURITY AUDIT"
echo "=================================================================="
echo ""

# 1. Kontrola .env v gite
echo "--- 1. Git ignore check ---"
if grep -q "^\.env" .gitignore 2>/dev/null; then
    log_ok ".env je v .gitignore"
else
    log_err ".env NIE JE v .gitignore!"
fi

# 2. Kontrola hardcoded secretov v zdrojaku
echo ""
echo "--- 2. Hardcoded secret scan ---"
if grep -rn "password.*=.*[^${}]" app/ --include="*.py" | grep -v "__pycache__" | grep -v "test" | grep -v "example" | head -5; then
    log_warn "Najdene potencialne hardcoded hodnoty (skontroluj vystup vyssie)"
else
    log_ok "Ziadne obvious hardcoded secrety v app/"
fi

# 3. Kontrola weak hesiel v .env
echo ""
echo "--- 3. Weak password check ---"
for f in .env .env.production; do
    if [ -f "$f" ]; then
        if grep -iE "(password|secret|key).*=(admin|password|123|secret|default|test)" "$f" 2>/dev/null; then
            log_err "Slabe heslo/secret v $f"
        else
            log_ok "$f — ziadne obvious weak hodnoty"
        fi
    fi
done

# 4. Kontrola dlzky JWT secretu
echo ""
echo "--- 4. JWT secret length ---"
if [ -f ".env.production" ]; then
    JWT_LEN=$(grep "^JWT_SECRET_KEY=" .env.production | cut -d= -f2 | tr -d '"' | wc -c || echo 0)
    if [ "$JWT_LEN" -lt 32 ]; then
        log_err "JWT_SECRET_KEY je prilis kratky ($JWT_LEN znakov)"
    else
        log_ok "JWT_SECRET_KEY dlzka OK ($JWT_LEN znakov)"
    fi
fi

# 5. Kontrola CORS
echo ""
echo "--- 5. CORS check ---"
if [ -f ".env.production" ]; then
    if grep -q "CORS_ALLOWED_ORIGINS.*\*" .env.production; then
        log_err "CORS_ALLOWED_ORIGINS obsahuje wildcard (*) — NEBEZPECNE!"
    else
        log_ok "CORS wildcard nie je pouzity"
    fi
fi

# Summary
echo ""
echo "=================================================================="
echo "📊 SUHRN: Errors=$ERRORS, Warnings=$WARNINGS"
echo "=================================================================="
if [ "$ERRORS" -gt 0 ]; then
    echo "❌ AUDIT ZLYHAL — oprav chyby!"
    exit 1
else
    echo "✅ AUDIT OK"
    exit 0
fi
