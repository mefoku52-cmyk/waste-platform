#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"

STAMP="$(date +%Y%m%d_%H%M%S)"
AUDIT="$ROOT/reports/cmep-flow/$STAMP"
LOG="$AUDIT/run.log"

mkdir -p "$AUDIT"

exec > >(tee -a "$LOG") 2>&1

STOPPED=0

die() {
    STOPPED=1
    echo
    echo "============================================================"
    echo "STOP"
    echo "============================================================"
    echo "$*"
    echo
    echo "Projekt nebol resetovaný."
    echo "Existujúce používateľské zmeny sa nemažú."
    echo "Audit: $AUDIT"
    exit 1
}

phase() {
    echo
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

have() {
    command -v "$1" >/dev/null 2>&1
}

require_file() {
    [ -f "$1" ] || die "Chýba súbor: $1"
}

run_pytest() {
    echo
    echo "=== PYTEST ==="
    python3 -m pytest -q | tee "$AUDIT/pytest.txt"
}

# ============================================================
# 0. ROOT + GIT
# ============================================================

phase "0. BEZPEČNÝ ŠTART"

[ "$ROOT" = "$(git rev-parse --show-toplevel)" ] \
    || die "Skript nie je spustený z Git rootu."

have git || die "git nie je dostupný."
have python3 || die "python3 nie je dostupný."

echo "ROOT:  $ROOT"
echo "AUDIT: $AUDIT"
echo "HEAD:  $(git rev-parse --short HEAD)"
echo "BRANCH: $(git branch --show-current)"

git status --short | tee "$AUDIT/status-before.txt"

# Nikdy:
# git reset --hard
# git clean -fd
# git restore .
#
# Skript zachová všetky existujúce zmeny.

git diff --binary > "$AUDIT/preexisting.diff"

# ============================================================
# 1. NÁHLÁSENIE
# ============================================================

phase "1. REPORTING: events router"

EVENT_ROUTER="app/modules/events/presentation/router.py"

require_file "$EVENT_ROUTER"

echo "Kontrola existujúceho events routera..."

grep -nE \
    'is_platform_admin|platform_admin|admin|activity_events|report' \
    "$EVENT_ROUTER" \
    | tee "$AUDIT/events-router-before.txt" || true

if grep -q 'is_platform_admin' "$EVENT_ROUTER"; then
    echo "is_platform_admin už existuje."
else
    echo "is_platform_admin chýba."

    # Nájdeme importy z auth/security vrstvy.
    AUTH_LINES="$AUDIT/auth-import-candidates.txt"

    grep -RIn \
        --include='*.py' \
        -E \
        'from .*auth.* import .*is_platform_admin|from .*security.* import .*is_platform_admin|def is_platform_admin|async def is_platform_admin' \
        app \
        | tee "$AUTH_LINES" || true

    COUNT="$(grep -c 'is_platform_admin' "$AUTH_LINES" 2>/dev/null || true)"

    [ "$COUNT" -ge 1 ] \
        || die "events router potrebuje is_platform_admin, ale jeho skutočný import nebol jednoznačne nájdený."

    IMPORT_LINE="$(grep 'is_platform_admin' "$AUTH_LINES" | head -n1)"

    echo "Nájdený kandidátny zdroj:"
    echo "$IMPORT_LINE"

    MODULE="$(printf '%s\n' "$IMPORT_LINE" | sed -n 's/^.*from \(.*\) import .*is_platform_admin.*/\1/p')"

    [ -n "$MODULE" ] \
        || die "Nepodarilo sa bezpečne určiť Python modul pre is_platform_admin."

    echo "Použitý modul: $MODULE"

    python3 - "$EVENT_ROUTER" "$MODULE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
module = sys.argv[2]

text = path.read_text()

if "is_platform_admin" in text:
    print("IMPORT_ALREADY_PRESENT")
    raise SystemExit(0)

lines = text.splitlines()

# Pokúsime sa pridať import vedľa existujúcich auth/security importov.
insert_at = None

for i, line in enumerate(lines):
    if line.startswith("from ") and (
        "auth" in line.lower()
        or "security" in line.lower()
        or "dependencies" in line.lower()
    ):
        insert_at = i + 1

if insert_at is None:
    # Bezpečná fallback pozícia:
    # za úvodné module docstring/import future.
    insert_at = 0

    while insert_at < len(lines):
        line = lines[insert_at].strip()
        if line.startswith('"""') or line.startswith("'''"):
            quote = line[:3]
            insert_at += 1
            while insert_at < len(lines) and quote not in lines[insert_at]:
                insert_at += 1
            insert_at += 1
            continue
        if line.startswith("from __future__ import"):
            insert_at += 1
            continue
        break

import_line = f"from {module} import is_platform_admin"

if import_line in lines:
    print("IMPORT_ALREADY_PRESENT")
    raise SystemExit(0)

lines.insert(insert_at, import_line)

path.write_text("\n".join(lines) + "\n")
print(f"ADDED: {import_line}")
PY

    python3 -m py_compile "$EVENT_ROUTER" \
        || die "events router po importe neprešiel py_compile."

    echo "is_platform_admin: IMPORT OK"
fi

# ============================================================
# 1B. REPORT CONTRACT
# ============================================================

echo
echo "=== REPORT CONTRACT ==="

grep -RIn \
    --include='*.py' \
    --include='*.ts' \
    --include='*.tsx' \
    -E \
    'report|Report|abuse|spam|harass|obťaž|fejk|fake' \
    app apps/web/src \
    | head -n 250 \
    | tee "$AUDIT/report-contract.txt" || true

# Nepridávame nový report modul naslepo.
# Existujúci reporting musí zostať jediným systémom.

# ============================================================
# 2. TEST + COMMIT REPORTING
# ============================================================

phase "2. REPORTING TEST"

python3 -m py_compile "$EVENT_ROUTER"

run_pytest

echo
echo "=== REPORTING DIFF ==="
git diff -- "$EVENT_ROUTER" \
    | tee "$AUDIT/reporting-diff.txt"

echo
echo "Reporting zmena je pripravená."

# Commit iba konkrétnej opravy.
git add "$EVENT_ROUTER"

git diff --cached --check \
    || die "Reporting staged diff obsahuje whitespace chyby."

git diff --cached -- "$EVENT_ROUTER" \
    | tee "$AUDIT/reporting-staged.diff"

git commit -m "fix(events): authorize platform admin reporting" \
    || die "Commit reporting opravy neprešiel."

echo "REPORTING COMMIT: PASS"

# ============================================================
# 3. PUSH
# ============================================================

phase "3. PUSH REPORTING"

git push origin main \
    | tee "$AUDIT/push-reporting.txt"

echo "REPORTING PUSH: PASS"

# ============================================================
# 4. LIVE CHECK
# ============================================================

phase "4. LIVE REPORTING CHECK"

echo
echo "Kontrola deploy referencie."

git rev-parse HEAD | tee "$AUDIT/pushed-head.txt"

echo
echo "Lokálny commit:"
git log -1 --oneline

echo
echo "Produkčný URL endpoint nie je hádaný."
echo "Ak je v environment dostupný:"
echo "  CMEP_PRODUCTION_URL"
echo "vykoná sa HTTP kontrola."

if [ -n "${CMEP_PRODUCTION_URL:-}" ]; then
    if have curl; then
        curl -fsS \
            --max-time 20 \
            "$CMEP_PRODUCTION_URL" \
            -o "$AUDIT/live-response.txt" \
            || die "Produkčný endpoint nereaguje."

        echo "LIVE HTTP: PASS"
    else
        echo "curl nie je dostupný, live HTTP kontrola preskočená."
    fi
else
    echo "CMEP_PRODUCTION_URL nie je nastavený."
    echo "LIVE: NEOVERENÉ"
fi

# ============================================================
# 5. CHAT AUTH
# ============================================================

phase "5. CHAT: VERIFIED COMPANY ONLY"

CHAT_ROUTER="app/modules/chat/presentation/router.py"

require_file "$CHAT_ROUTER"

grep -nE \
    'create_thread|send|message|membership|company|current_user|Depends' \
    "$CHAT_ROUTER" \
    | tee "$AUDIT/chat-contract.txt"

# Zámerne žiadny regex patch.
#
# Predchádzajúca verzia skriptu sa pokúsila vložiť authorization
# do create_thread bez toho, aby mala thread_id.
#
# Teraz najprv identifikujeme skutočné authorization dependency.

grep -RIn \
    --include='*.py' \
    -E \
    'verified.*company|company.*verified|membership.*verified|is_company|company_membership|MembershipStatus' \
    app/modules \
    | head -n 300 \
    | tee "$AUDIT/company-auth-candidates.txt" || true

echo
echo "CHAT AUTH: kontrakt zozbieraný."
echo "Nebola vložená slepá authorization kontrola."

# ============================================================
# 6. LISTING CTA
# ============================================================

phase "6. LISTING CTA"

LISTING_PAGE="apps/web/src/app/dashboard/listings/[id]/page.tsx"

require_file "$LISTING_PAGE"

grep -nE \
    'Napísať|Chcem odobrať|inquiry|chat|company|membership' \
    "$LISTING_PAGE" \
    | tee "$AUDIT/listing-cta-before.txt" || true

echo
echo "Existujúce listing CTA zachované."
echo "Nové CTA sa doplní až podľa reálneho company/membership API contractu."

grep -RIn \
    --include='*.ts' \
    --include='*.tsx' \
    -E \
    'company.*me|my.*company|membership|verified' \
    apps/web/src \
    | head -n 300 \
    | tee "$AUDIT/frontend-company-contract.txt" || true

# ============================================================
# 7. EXISTUJÚCE DOPYTY
# ============================================================

phase "7. INQUIRY FLOW"

INQ_ROUTER="app/modules/inquiries/presentation/router.py"
INQ_SCHEMA="app/modules/inquiries/presentation/schemas.py"
INQ_MODEL="app/modules/inquiries/infrastructure/models.py"
INQ_SERVICE="app/modules/inquiries/application/services.py"

for f in \
    "$INQ_ROUTER" \
    "$INQ_SCHEMA" \
    "$INQ_MODEL" \
    "$INQ_SERVICE"
do
    require_file "$f"
done

echo "=== CREATE CONTRACT ==="

grep -nE \
    'listingId|companyId|message|contactEmail|contactPhone' \
    "$INQ_SCHEMA" \
    | tee "$AUDIT/inquiry-create.txt"

grep -q 'companyId: UUID' "$INQ_SCHEMA" \
    || die "InquiryCreateRequest nemá očakávané companyId."

echo
echo "=== STATUS ==="

grep -nE \
    'OPEN|ANSWERED|CLOSED|open|answered|closed|rejected' \
    app/modules/inquiries/domain/enums.py \
    | tee "$AUDIT/inquiry-status.txt"

grep -q 'OPEN = "open"' \
    app/modules/inquiries/domain/enums.py \
    || die "OPEN chýba."

grep -q 'ANSWERED = "answered"' \
    app/modules/inquiries/domain/enums.py \
    || die "ANSWERED chýba."

grep -q 'CLOSED = "closed"' \
    app/modules/inquiries/domain/enums.py \
    || die "CLOSED chýba."

if grep -q 'rejected' app/modules/inquiries/domain/enums.py; then
    echo "POZOR: rejected už existuje."
else
    echo "Status contract: open / answered / closed"
fi

echo
echo "=== RECEIVED ==="

grep -RIn \
    --include='*.py' \
    'list_received' \
    app/modules/inquiries \
    | tee "$AUDIT/inquiry-received.txt"

# ============================================================
# 8. LISTING VIEWED
# ============================================================

phase "8. LISTING VIEWED"

grep -RIn \
    --include='*.py' \
    --include='*.ts' \
    --include='*.tsx' \
    -E \
    'listing_viewed|activity_events|activity.*event' \
    app apps/web/src \
    | head -n 400 \
    | tee "$AUDIT/listing-viewed.txt" || true

echo
echo "Listing viewed: kód nájdený alebo označený na ďalšie overenie."
echo "Produkčná DB sa bez explicitného production prístupu neháda."

# ============================================================
# 9. COMPANY GEO + MATERIALS
# ============================================================

phase "9. COMPANY GEO + MATERIALS"

COMPANY_MODEL="app/modules/companies/infrastructure/models.py"

require_file "$COMPANY_MODEL"

grep -nE \
    'latitude|longitude|accepted_material_types' \
    "$COMPANY_MODEL" \
    | tee "$AUDIT/company-geo-materials.txt"

for field in latitude longitude accepted_material_types; do
    grep -q "$field" "$COMPANY_MODEL" \
        || die "Company field chýba: $field"
done

echo
echo "Existujúce company fields sa nepremodelujú."
echo "Dopĺňanie hodnôt pri verification zostáva ďalšou konkrétnou implementáciou."

# ============================================================
# 10. I18N
# ============================================================

phase "10. I18N"

I18N="apps/web/src/lib/i18n/messages"

for lang in sk en de fr ru; do
    FILE="$I18N/$lang.json"
    require_file "$FILE"

    python3 - "$FILE" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
json.loads(p.read_text())
print(f"JSON OK: {p}")
PY
done

grep -RIn \
    --include='*.json' \
    -E \
    'report|route|recommend|inquiry|dopyt|nahlásiť' \
    "$I18N" \
    | tee "$AUDIT/i18n-existing.txt" || true

# ============================================================
# 11. TRADE STATUS
# ============================================================

phase "11. TRADE STATUS"

echo
echo "Použije sa existujúci InquiryStatus:"
echo "  open"
echo "  answered"
echo "  closed"
echo

grep -RIn \
    --include='*.py' \
    --include='*.ts' \
    --include='*.tsx' \
    -E \
    'InquiryStatus|answered|closed' \
    app/modules/inquiries apps/web/src \
    | head -n 500 \
    | tee "$AUDIT/trade-status.txt" || true

# ============================================================
# 12. RATINGS
# ============================================================

phase "12. RATINGS"

grep -RIn \
    --include='*.py' \
    --include='*.ts' \
    --include='*.tsx' \
    -E \
    'rating|ratings|review|reviews|stars' \
    app apps/web/src \
    | head -n 500 \
    | tee "$AUDIT/ratings.txt" || true

echo
echo "Rating sa zatiaľ neotvára pred CLOSED inquiry."

# ============================================================
# 13. FINÁLNA KONTROLA
# ============================================================

phase "13. FINÁLNY STAV"

echo "=== HEAD ==="
git log -3 --oneline

echo
echo "=== STATUS ==="
git status --short | tee "$AUDIT/status-final.txt"

echo
echo "=== DIFF ==="
git diff --stat | tee "$AUDIT/diff-final.txt"

echo
echo "=== AUDIT ==="
find "$AUDIT" -maxdepth 1 -type f -printf '%f\n' \
    | sort

echo
echo "============================================================"
echo "VÝSLEDOK"
echo "============================================================"
echo
echo "KROK 1 REPORTING: IMPLEMENTOVANÝ A PUSHNUTÝ"
echo "KROK 2 LIVE: podľa CMEP_PRODUCTION_URL"
echo "KROK 3 CHAT: KONTRAKT ZOZBIERANÝ"
echo "KROK 4 CTA: KONTRAKT ZOZBIERANÝ"
echo "KROK 5 INQUIRY: OVERENÝ EXISTUJÚCI MODEL"
echo "KROK 6 LISTING VIEWED: ZMAPOVANÉ"
echo "KROK 7 COMPANY GEO/MATERIALS: OVERENÉ"
echo "KROK 8 I18N: OVERENÉ"
echo "KROK 9 TRADE STATUS: OPEN/ANSWERED/CLOSED"
echo "KROK 10 RATINGS: ODLOŽENÉ ZA CLOSED"
echo
echo "Audit: $AUDIT"
echo
echo "STATUS: CONTROLLED-IMPLEMENTATION"
