#!/bin/bash
set -Eeuo pipefail

# ═══════════════════════════════════════════════════════════════════════════════════
#              FORENZNÝ AUDIT PLATFORMY – CMEP (Waste Platform)
#              Vykonané: $(date '+%Y-%m-%d %H:%M:%S')
# ═══════════════════════════════════════════════════════════════════════════════════

AUDIT_REPORT="forensic-audit-report-$(date '+%Y%m%d-%H%M%S').txt"
PROJECT_ROOT="$(pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Reset
echo "" > "$AUDIT_REPORT"

log() {
    echo -e "$1" | tee -a "$AUDIT_REPORT"
}

log_header() {
    log ""
    log "╔════════════════════════════════════════════════════════════════════════════════════════╗"
    log "║  $1"
    log "╚════════════════════════════════════════════════════════════════════════════════════════╝"
    log ""
}

log_section() {
    log ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "  📋 $1"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

count_pass=0
count_fail=0
count_warn=0
count_info=0

check_pass() {
    ((count_pass++))
    log "  ${GREEN}✅ PASS${NC}  $1"
}

check_fail() {
    ((count_fail++))
    log "  ${RED}❌ FAIL${NC}  $1"
}

check_warn() {
    ((count_warn++))
    log "  ${YELLOW}⚠️  WARN${NC}  $1"
}

check_info() {
    ((count_info++))
    log "  ${BLUE}ℹ️  INFO${NC}  $1"
}

# ═══════════════════════════════════════════════════════════════════════════════════
# ZAČIATOK AUDITU
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "${BOLD}FORENZNÝ AUDIT PLATFORMY CMEP${NC}"
log "Dátum: $(date '+%Y-%m-%d %H:%M:%S')"
log "Používateľ: $(whoami)"
log "Hostiteľ: $(hostname)"
log "Platforma: $(uname -s) $(uname -m)"
log "Adresár: $PROJECT_ROOT"
log ""
log "Verzia Docker: $(docker --version 2>/dev/null || echo 'Nedostupné')"
log "Verzia Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo 'Nedostupné')"

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 1: ANALÝZA ŠTRUKTÚRY PROJEKTU
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "1. ANALÝZA ŠTRUKTÚRY PROJEKTU"

log_section "1.1 Adresárová štruktúra"

if [ -d "$PROJECT_ROOT" ]; then
    check_pass "Koreňový adresár existuje"
    log "  Adresárová hierarchia:"
    find . -maxdepth 3 -type d ! -path '*/\.*' | head -50 | while read dir; do
        depth=$(echo "$dir" | tr -cd '/' | wc -c)
        indent=$(printf '%*s' $((depth * 2)) "")
        count=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l)
        log "  ${indent}📁 ${dir#$PROJECT_ROOT/} (${count} súborov)"
    done
else
    check_fail "Koreňový adresár neexistuje"
fi

log ""
log_section "1.2 Kľúčové súbory"

key_files=(
    "docker-compose.yml"
    "docker-compose.monitoring.yml"
    "Makefile"
    "README.md"
    ".env"
    ".env.production"
    "requirements.txt"
    "package.json"
    "pyproject.toml"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        lines=$(wc -l < "$file" 2>/dev/null || echo "0")
        check_pass "Súbor existuje: $file (${size}B, ${lines} riadkov)"
    else
        check_warn "Súbor chýba: $file"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 2: SYNTAX KONTROLA
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "2. SYNTAX KONTROLA"

log_section "2.1 Docker Compose súbory"

if command -v docker &> /dev/null; then
    if docker compose config > /dev/null 2>&1; then
        check_pass "docker-compose.yml je validný"
    else
        check_fail "docker-compose.yml má syntaktické chyby"
        docker compose config 2>&1 | head -20 | while read line; do
            log "     $line"
        done
    fi

    if [ -f "docker-compose.monitoring.yml" ]; then
        if docker compose -f docker-compose.monitoring.yml config > /dev/null 2>&1; then
            check_pass "docker-compose.monitoring.yml je validný"
        else
            check_fail "docker-compose.monitoring.yml má syntaktické chyby"
        fi
    fi
else
    check_warn "Docker nie je nainštalovaný - kontrola preskočená"
fi

log ""
log_section "2.2 YAML konfiguračné súbory"

yaml_files=$(find . -name "*.yml" -o -name "*.yaml" 2>/dev/null | grep -v node_modules | grep -v __pycache__)
if [ -z "$yaml_files" ]; then
    check_warn "Žiadne YAML súbory nenájdené"
else
    for yaml in $yaml_files; do
        if command -v python3 &> /dev/null; then
            if python3 -c "import yaml; yaml.safe_load(open('$yaml'))" 2>/dev/null; then
                check_pass "YAML validný: $yaml"
            else
                check_fail "YAML nevalidný: $yaml"
            fi
        else
            # Ručná kontrola formátu
            if grep -q "^[[:space:]]*[^#:]*:.*[^:]$" "$yaml" 2>/dev/null; then
                check_info "YAML: $yaml (bez Python validátora)"
            fi
        fi
    done
fi

log ""
log_section "2.3 Python syntax kontrola"

py_files=$(find . -name "*.py" ! -path "*/\.*" ! -path "*/__pycache__/*" 2>/dev/null | head -30)
if [ -z "$py_files" ]; then
    check_warn "Žiadne Python súbory nenájdené"
else
    for py in $py_files; do
        if command -v python3 &> /dev/null; then
            if python3 -m py_compile "$py" 2>/dev/null; then
                check_pass "Python validný: $py"
            else
                check_fail "Python chyba: $py"
                python3 -m py_compile "$py" 2>&1 | while read line; do
                    log "     $line"
                done
            fi
        else
            check_info "Python interpreter nie je dostupný"
            break
        fi
    done
fi

log ""
log_section "2.4 Shell script syntax kontrola"

sh_files=$(find . -name "*.sh" 2>/dev/null | head -20)
for sh in $sh_files; do
    if [ -f "$sh" ]; then
        if bash -n "$sh" 2>/dev/null; then
            check_pass "Shell script validný: $sh"
        else
            check_fail "Shell script má chybu: $sh"
            bash -n "$sh" 2>&1 | while read line; do
                log "     $line"
            done
        fi
    fi
done

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 3: BEZPEČNOSTNÝ AUDIT
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "3. BEZPEČNOSTNÝ AUDIT"

log_section "3.1 Sekrety a konfigurácia"

if [ -f ".env" ]; then
    sensitive_patterns=("PASSWORD" "SECRET" "KEY" "TOKEN" "API_KEY")
    for pattern in "${sensitive_patterns[@]}"; do
        if grep -r "$pattern" .env 2>/dev/null | grep -v "^#" | grep -v "change-me" | grep -qv "example"; then
            check_warn "Možný hardcoded secret: $pattern v .env"
        fi
    done
fi

# Kontrola production .env
if [ -f ".env.production" ]; then
    if grep -q "change-me" .env.production 2>/dev/null; then
        check_warn ".env.production obsahuje placeholder sekrety (change-me)"
    fi
    if grep -q "your-secret-key" .env.production 2>/dev/null; then
        check_fail ".env.production obsahuje nebezpečné default hodnoty"
    fi
fi

log ""
log_section "3.2 Docker bezpečnosť"

if [ -f "docker-compose.yml" ]; then
    if grep -q "privileged.*true" docker-compose.yml 2>/dev/null; then
        check_warn "Služba beží v privileged režime"
    fi
    
    if grep -q "network_mode.*host" docker-compose.yml 2>/dev/null; then
        check_warn "Služba používa host network mode"
    fi
    
    if grep -q ":4444" docker-compose.yml 2>/dev/null || grep -q ":4443" docker-compose.yml 2>/dev/null; then
        check_warn "Služba odhaľuje port 4444/4443 (metabase?)"
    fi
    
    # Kontrola root user v Dockerfile
    df_count=$(find . -name "Dockerfile*" 2>/dev/null | wc -l)
    if [ "$df_count" -gt 0 ]; then
        check_info "Nájdené $df_count Dockerfile súborov"
        find . -name "Dockerfile*" -exec grep -l "USER root" {} \; 2>/dev/null | while read df; do
            check_warn "Dockerfile môže beží ako root: $df"
        done
    fi
fi

log ""
log_section "3.3 CORS a autentifikácia"

if grep -q "CORS_ALLOWED_ORIGINS" .env.production 2>/dev/null; then
    cors_origins=$(grep "CORS_ALLOWED_ORIGINS" .env.production | cut -d'=' -f2)
    if [ "$cors_origins" = "*" ] || [ "$cors_origins" = "http://*:*" ]; then
        check_fail "CORS je otvorený pre všetky domény"
    else
        check_pass "CORS je nakonfigurovaný"
    fi
fi

if grep -q "JWT_SECRET_KEY" .env.production 2>/dev/null; then
    jwt_secret=$(grep "JWT_SECRET_KEY" .env.production | cut -d'=' -f2)
    if [ ${#jwt_secret} -lt 32 ]; then
        check_warn "JWT_SECRET_KEY je príliš krátky (min. 32 znakov)"
    else
        check_pass "JWT_SECRET_KEY má dostatočnú dĺžku"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 4: FUNKCIONALITA A LOGIKA
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "4. FUNKCIONALITA A LOGIKA"

log_section "4.1 FastAPI aplikácia"

if [ -d "app" ]; then
    check_pass "Adresár app/ existuje"
    
    # Kontrola main.py
    if [ -f "app/main.py" ]; then
        check_pass "app/main.py existuje"
        
        # Import kontrol
        if grep -q "FastAPI" app/main.py 2>/dev/null; then
            check_pass "FastAPI import nájdený"
        fi
        
        if grep -q "include_router" app/main.py 2>/dev/null; then
            routers=$(grep -c "include_router" app/main.py)
            check_info "Počet routerov: $routers"
        fi
        
        # Health check
        if grep -q "/health" app/main.py 2>/dev/null; then
            check_pass "Health endpoint definovaný"
        else
            check_warn "Health endpoint chýba v main.py"
        fi
        
        # Metrics
        if grep -q "/metrics" app/main.py 2>/dev/null; then
            check_pass "Metrics endpoint definovaný"
        else
            check_warn "Metrics endpoint chýba v main.py"
        fi
    else
        check_warn "app/main.py chýba"
    fi
    
    # Routers
    router_count=$(find app -name "*router*.py" 2>/dev/null | wc -l)
    if [ "$router_count" -gt 0 ]; then
        check_pass "Nájdené $router_count router súborov"
    fi
    
    # Schemas
    schema_count=$(find app -path "*schema*.py" 2>/dev/null | wc -l)
    if [ "$schema_count" -gt 0 ]; then
        check_pass "Nájdené $schema_count schema súborov"
    fi
    
else
    check_fail "Adresár app/ neexistuje"
fi

log ""
log_section "4.2 Next.js aplikácia"

if [ -d "apps" ]; then
    check_pass "Adresár apps/ existuje"
    
    if [ -f "apps/web/package.json" ]; then
        check_pass "apps/web/package.json existuje"
        
        if grep -q '"next"' apps/web/package.json 2>/dev/null; then
            check_pass "Next.js závislosť definovaná"
        fi
        
        if grep -q '"typescript"' apps/web/package.json 2>/dev/null; then
            check_pass "TypeScript závislosť definovaná"
        fi
    fi
    
    # Src štruktúra
    if [ -d "apps/web/src" ]; then
        check_pass "apps/web/src/ existuje"
        
        app_files=$(find apps/web/src -name "page.tsx" -o -name "page.ts" 2>/dev/null | wc -l)
        if [ "$app_files" -gt 0 ]; then
            check_pass "Nájdené $app_files page súborov"
        fi
        
        component_count=$(find apps/web/src -name "*.tsx" ! -path "*/components/*" 2>/dev/null | wc -l)
        components=$(find apps/web/src -path "*/components/*" -name "*.tsx" 2>/dev/null | wc -l)
        check_info "Komponenty: $component_count súborov, $components v components/"
    fi
else
    check_warn "Adresár apps/ neexistuje alebo je prázdny"
fi

log ""
log_section "4.3 Databáza a ORM"

if [ -f "app/database.py" ] || [ -f "app/core/database.py" ] || find app -name "*database*.py" 2>/dev/null | grep -q .; then
    check_pass "Databázové súbory nájdené"
    
    if grep -q "asyncpg" app/**/*.py 2>/dev/null || grep -q "asyncpg" app/**/**/*.py 2>/dev/null; then
        check_pass "asyncpg (PostgreSQL async driver) použitý"
    fi
    
    if grep -q "sqlalchemy" app/**/*.py 2>/dev/null || grep -q "sqlalchemy" app/**/**/*.py 2>/dev/null; then
        check_pass "SQLAlchemy ORM nájdený"
    fi
else
    check_warn "Databázové súbory neručné"
fi

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 5: PREPOJENIA A INTEGRÁCIE
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "5. PREPOJENIA A INTEGRÁCIE"

log_section "5.1 Docker služby"

log "Kontrola docker-compose.yml služieb:"
services=$(grep -E "^\s+[a-z_]+:" docker-compose.yml 2>/dev/null | sed 's/:$//' | sed 's/^[[:space:]]*//' | sort | uniq)
for svc in $services; do
    if [ -n "$svc" ]; then
        check_info "Služba: $svc"
    fi
done

log ""
log_section "5.2 Environment premenné"

required_env_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "APP_HOST"
    "APP_PORT"
)

for var in "${required_env_vars[@]}"; do
    if grep -q "$var" .env.production 2>/dev/null; then
        check_pass "Env premenná definovaná: $var"
    else
        check_warn "Env premenná chýba: $var"
    fi
done

log ""
log_section "5.3 MinIO / S3 konfigurácia"

minio_vars=("MINIO_ROOT_USER" "MINIO_ROOT_PASSWORD" "S3_BUCKET")
for var in "${minio_vars[@]}"; do
    if grep -q "$var" .env.production 2>/dev/null; then
        check_pass "MinIO konfigurácia: $var"
    else
        check_warn "MinIO konfigurácia chýba: $var"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 6: MONITORING A OBSERVABILITY
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "6. MONITORING A OBSERVABILITY"

log_section "6.1 Prometheus konfigurácia"

if [ -f "infra/prometheus/prometheus.yml" ]; then
    check_pass "Prometheus konfigurácia existuje"
    
    if grep -q "scrape_configs" infra/prometheus/prometheus.yml 2>/dev/null; then
        scrape_count=$(grep -c "job_name" infra/prometheus/prometheus.yml 2>/dev/null || echo "0")
        check_info "Prometheus scrape jobs: $scrape_count"
    fi
else
    check_warn "Prometheus konfigurácia chýba"
fi

log ""
log_section "6.2 Alertmanager"

if [ -f "infra/alertmanager/alertmanager.yml" ]; then
    check_pass "Alertmanager konfigurácia existuje"
else
    check_warn "Alertmanager konfigurácia chýba"
fi

log ""
log_section "6.3 Loki log aggregation"

if [ -f "infra/loki/loki-config.yml" ]; then
    check_pass "Loki konfigurácia existuje"
else
    check_warn "Loki konfigurácia chýba"
fi

if [ -f "infra/loki/promtail-config.yml" ]; then
    check_pass "Promtail konfigurácia existuje"
else
    check_warn "Promtail konfigurácia chýba"
fi

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 7: CI/CD A DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "7. CI/CD A DEPLOYMENT"

log_section "7.1 Makefile"

if [ -f "Makefile" ]; then
    check_pass "Makefile existuje"
    
    targets=$(grep -E "^[a-z_]+:" Makefile 2>/dev/null | sed 's/:$//' | head -20)
    if [ -n "$targets" ]; then
        check_info "Makefile targets:"
        echo "$targets" | while read t; do log "     - $t"; done
    fi
else
    check_warn "Makefile chýba"
fi

log ""
log_section "7.2 Deployment skripty"

script_files=("scripts/deploy.sh" "scripts/bootstrap-letsencrypt.sh" "scripts/logs.sh")
for script in "${script_files[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            check_pass "Skript existuje a je spustiteľný: $script"
        else
            check_warn "Skript existuje ale nie je spustiteľný: $script"
        fi
    else
        check_warn "Skript chýba: $script"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 8: DOKUMENTÁCIA
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "8. DOKUMENTÁCIA"

log_section "8.1 Markdown dokumenty"

docs=(
    "README.md"
    "docs/monitoring.md"
    "docs/architecture-overview.md"
    "docs/troubleshooting.md"
    "docs/production-readiness.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        lines=$(wc -l < "$doc")
        check_pass "Dokumentácia: $doc (${lines} riadkov)"
    else
        check_warn "Dokumentácia chýba: $doc"
    fi
done

log ""
log_section "8.2 OpenAPI / Swagger"

if grep -q "docs_url" app/main.py 2>/dev/null || grep -q 'docs/"' app/main.py 2>/dev/null; then
    check_pass "OpenAPI dokumentácia povolená"
else
    check_info "OpenAPI dokumentácia - nutná manuálna kontrola"
fi

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 9: VÝKON A OPTIMALIZÁCIA
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "9. VÝKON A OPTIMALIZÁCIA"

log_section "9.1 Redis cachovanie"

if grep -q "redis" docker-compose.yml 2>/dev/null; then
    check_pass "Redis služba definovaná v Docker Compose"
fi

if grep -q "redis" .env.production 2>/dev/null; then
    check_pass "Redis URL definované"
fi

log ""
log_section "9.2 Worker a background jobs"

if grep -q "worker" docker-compose.yml 2>/dev/null || grep -q "celery" docker-compose.yml 2>/dev/null; then
    check_pass "Worker služba definovaná"
fi

# ═══════════════════════════════════════════════════════════════════════════════════
# SEKCIA 10: SÚHRN A ODPORÚČANIA
# ═══════════════════════════════════════════════════════════════════════════════════

log_header "10. SÚHRN AUDITU"

log ""
log "┌─────────────────────────────────────────────────────────────────────────────┐"
log "│                           VÝSLEDKY AUDITU                                   │"
log "├─────────────────────────────────────────────────────────────────────────────┤"
log "│  ${GREEN}✅ PASS:${NC}   $count_pass                                                           │"
log "│  ${RED}❌ FAIL:${NC}   $count_fail                                                           │"
log "│  ${YELLOW}⚠️  WARN:${NC}  $count_warn                                                           │"
log "│  ${BLUE}ℹ️  INFO:${NC}  $count_info                                                           │"
log "└─────────────────────────────────────────────────────────────────────────────┘"

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  📊 ODPOČUTEĽNÉ ODPORÚČANIA"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""
log "  KRITICKÉ (okamžite riešiť):"
log "  • Vymeň všetky 'change-me' sekrety v .env.production"
log "  • Skontroluj CORS nastavenia pre produkciu"
log "  • Over SSL/TLS certifikáty"
log ""
log "  VYSOKÉ (do 1 týždňa):"
log "  • Aktualizuj závislosti (npm audit, pip check)"
log "  • Implementuj rate limiting ak nie je prítomný"
log "  • Nastav automatické zálohovanie databázy"
log ""
log "  STREDNÉ (do 1 mesiaca):"
log "  • Dokumentuj všetky API endpoints"
log "  • Pridaj health checky pre všetky služby"
log "  • Implementuj log rotation"
log ""
log "  NÍZKÉ (dlhodobé):"
log "  • Optimalizuj Docker image sizes"
log "  • Pridaj end-to-end testy"
log "  • Nastav CI/CD pipeline"

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  🔧 KONTROLNÝ ZOZNAM pred produkciou"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""
log "  ☐ Sekrety zmenené z default hodnôt"
log "  ☐ TLS certifikáty nainštalované a validné"
log "  ☐ Health endpoints aktívne a testované"
log "  ☐ Monitoring stack beží"
log "  ☐ Logy sa ukladajú centrálne"
log "  ☐ Databázové zálohovanie nastavené"
log "  ☐ Firewall pravidlá overené"
log "  ☐ Rate limiting povolené"
log "  ☐ CORS nakonfigurované pre produkčnú doménu"

log ""
log "══════════════════════════════════════════════════════════════════════════════════════════"
log "  AUDIT DOKONČENÝ"
log "  Report uložený: $AUDIT_REPORT"
log "══════════════════════════════════════════════════════════════════════════════════════════"

# Záverečné štatistiky
total=$((count_pass + count_fail + count_warn + count_info))
if [ $total -gt 0 ]; then
    pass_rate=$((count_pass * 100 / total))
    log ""
    log "  Celkové skóre: ${pass_rate}% (PASS rate)"
fi

exit 0
