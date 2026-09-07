#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/waste-platform"
cd "$ROOT" || exit 1

echo "============================================================"
echo "R60 -> R61 AUTHORITY LINK DISCOVERY"
echo "============================================================"
echo "DATE=$(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJECT=$ROOT"
echo "MODE=READ_ONLY"
echo "============================================================"

echo
echo "============================================================"
echo "1. DIRECT R60/R61 REFERENCES"
echo "============================================================"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude='inspect_r60_r61_authority_link.sh' \
    --exclude='R60_R65_FORENSIC_RECONCILIATION_*.txt' \
    '(R60[^A-Za-z0-9_]*R61|R61[^A-Za-z0-9_]*R60|R60.*R61|R61.*R60)' \
    "$ROOT" 2>/dev/null |
head -500 || true

echo
echo "============================================================"
echo "2. REMEDIATION / RESOLUTION REFERENCES AROUND R60"
echo "============================================================"

grep -RInEi \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude='inspect_r60_r61_authority_link.sh' \
    --exclude='R60_R65_FORENSIC_RECONCILIATION_*.txt' \
    '(R60.{0,160}(remediat|resolved|closed|fixed|fix|repair|supersed|replace|address)|'\
'remediat.{0,160}R60|'\
'resolved.{0,160}R60|'\
'R61.{0,160}(remediat|resolved|closed|fixed|fix|repair|supersed|replace|address))' \
    "$ROOT" 2>/dev/null |
head -500 || true

echo
echo "============================================================"
echo "3. R61 STATUS / RESULT / VERDICT SIGNALS"
echo "============================================================"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude='inspect_r60_r61_authority_link.sh' \
    --exclude='R60_R65_FORENSIC_RECONCILIATION_*.txt' \
    '^(R61|P0).*|STATUS=.*|RESULT=.*|VERDICT=.*|EXIT_CODE=.*|PASS=.*|FAIL=.*|BLOCKED=.*|OPEN=.*|CLOSED=.*' \
    "$ROOT" 2>/dev/null |
head -500 || true

echo
echo "============================================================"
echo "4. R60 STATUS / RESULT / VERDICT SIGNALS"
echo "============================================================"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude='inspect_r60_r61_authority_link.sh' \
    --exclude='R60_R65_FORENSIC_RECONCILIATION_*.txt' \
    'R60_TEST_STATUS=|R60.*STATUS|R60.*RESULT|R60.*VERDICT|R60.*FAIL|R60.*PASS|R60.*BLOCKED|R60.*OPEN|R60.*CLOSED' \
    "$ROOT" 2>/dev/null |
head -500 || true

echo
echo "============================================================"
echo "5. R61 BACKUP METADATA / TIMESTAMPS"
echo "============================================================"

R61="$ROOT/.production-release/r61-backup-20260903_104708"

if [ -d "$R61" ]; then
    stat "$R61" 2>/dev/null || true
    echo
    find "$R61" -maxdepth 1 -type f -exec stat -c '%y|%n' {} \; 2>/dev/null | sort
else
    echo "R61=NOT_FOUND"
fi

echo
echo "============================================================"
echo "6. FILE NAMES SUGGESTING R60/R61 RELATION"
echo "============================================================"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    ! -path '*/__pycache__/*' \
    -printf '%p\n' 2>/dev/null |
grep -Ei '(r60|r61|remediat|closure|decision|truth|reconcil|release)' |
head -500 || true

echo
echo "============================================================"
echo "7. AUTHORITY INTERPRETATION"
echo "============================================================"

echo "R60_CURRENT_FAILURES=5"
echo "R61_STRUCTURAL_CORRESPONDENCE=ESTABLISHED"
echo "R61_OFFICIAL_REMEDIATION_LINK=NOT_YET_ESTABLISHED"
echo
echo "DO NOT infer CLOSED from temporal order."
echo "DO NOT modify project files."
echo "DO NOT create R66."
echo
echo "NO_REMEDIATION=YES"
echo "NO_R66=YES"
echo "NO_PROJECT_MODIFICATION=YES"
echo "============================================================"
