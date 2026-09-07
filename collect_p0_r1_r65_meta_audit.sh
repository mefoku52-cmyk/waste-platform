#!/usr/bin/env bash
set -u

OUT="P0_R1_R65_META_AUDIT_$(date +%Y%m%d_%H%M%S).txt"

exec > >(tee "$OUT") 2>&1

echo "============================================================"
echo "P0 → R1-R65 META-AUDIT COLLECTION"
echo "============================================================"
echo "DATE=$(date -Is)"
echo "PWD=$(pwd)"
echo

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

section "1. PROJECT IDENTITY"

printf 'GIT_BRANCH='
git branch --show-current 2>/dev/null || true

printf 'GIT_HEAD='
git rev-parse --short HEAD 2>/dev/null || true

printf 'GIT_STATUS='
git status --short 2>/dev/null | head -40 || true

printf 'PROJECT_FILES='
find . -maxdepth 2 -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    | wc -l

section "2. ALL P/R GATE FILES"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( \
        -iname '*phase*p0*' -o \
        -iname '*phase*r[0-9]*' -o \
        -iname '*r[0-9]*gate*' -o \
        -iname '*r[0-9]*status*' -o \
        -iname '*r[0-9]*audit*' \
    \) \
    -print 2>/dev/null \
    | sort -V

section "3. R-NUMBER INVENTORY FROM FILENAMES"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    -print 2>/dev/null \
    | grep -Eio '(^|/)([^/]*)(r[0-9]{1,2})([^/]*)$' \
    | grep -Eio 'r[0-9]{1,2}' \
    | sort -V \
    | uniq -c

section "4. P0 / R HEADERS AND TITLES"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    '(^|[[:space:][:punct:]])(P0|R[0-9]{1,2})[[:space:]_-].{0,180}$' \
    . 2>/dev/null \
    | head -500

section "5. STATUS / RESULT / EXIT_CODE SIGNALS"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    '(STATUS|RESULT|EXIT_CODE|REPORT|VERDICT|PASS|FAIL|FAILED|SUCCESS|ERROR|WARN|WARNING|BLOCKED|SKIPPED|OPEN|CLOSED|INCONCLUSIVE)[[:space:]]*=' \
    . 2>/dev/null \
    | head -800

section "6. GATE SCRIPT INTERNAL IDENTIFIERS"

grep -RInE \
    --include='*.sh' \
    --include='*.bash' \
    --include='*.py' \
    --include='*.yml' \
    --include='*.yaml' \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    '(P0-[0-9]+|R[0-9]{1,2})[[:space:]_-]+[A-Z][A-Z0-9 _:-]{3,120}' \
    . 2>/dev/null \
    | head -800

section "7. LOG / REPORT FILE INVENTORY"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( \
        -iname '*.log' -o \
        -iname '*report*' -o \
        -iname '*audit*' -o \
        -iname '*result*' -o \
        -iname '*status*' -o \
        -iname '*verdict*' \
    \) \
    -printf '%p\t%s bytes\t%TY-%Tm-%Td %TH:%TM:%TS\n' \
    2>/dev/null \
    | sort -V \
    | tail -300

section "8. RECENT LOG TAILS ONLY"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( -iname '*.log' -o -iname '*report*' -o -iname '*result*' \) \
    -size -5M \
    -print 2>/dev/null \
    | sort -V \
    | while read -r f; do
        echo
        echo "--- FILE: $f ---"
        tail -40 "$f" 2>/dev/null || true
      done

section "9. SCRIPT EXECUTION / CREATION ORDER"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( -name '*.sh' -o -name '*.bash' \) \
    -printf '%T@ %TY-%Tm-%Td %TH:%TM:%TS %p\n' \
    2>/dev/null \
    | sort -n \
    | grep -Ei \
        'p0|r[0-9]{1,2}|phase|gate|audit|provenance|registry|secret|reconcil|stability' \
    | tail -300

section "10. R1-R65 PRESENCE MATRIX"

for n in $(seq 1 65); do
    hits=$(
        find . -type f \
            -not -path './.git/*' \
            -not -path './.venv/*' \
            -not -path './node_modules/*' \
            -print 2>/dev/null \
            | grep -Ei \
                "(^|[/_.-])r0*${n}([_.-]|[/]|$)" \
            | head -20
    )

    if [ -n "$hits" ]; then
        echo "R${n}=PRESENT"
        echo "$hits" | sed 's/^/  /'
    else
        echo "R${n}=NOT_FOUND_BY_FILENAME"
    fi
done

section "11. REFERENCES BETWEEN R-GATES"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    'R[0-9]{1,2}[[:space:]]*(→|->|TO|AFTER|BEFORE|NEXT|PREVIOUS|FOLLOW|DEPENDS|DEPENDENCY|PREREQUISITE|BLOCKS|BLOCKED)' \
    . 2>/dev/null \
    | head -500

section "12. EXPLICIT P0 REFERENCES"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    '(P0-[0-9]+|P0_?[0-9]+|PHASE_P0)' \
    . 2>/dev/null \
    | head -500

section "13. GATE RESULT KEYWORDS"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    '(PASS|FAIL|FAILED|SUCCESS|ERROR|BLOCKED|SKIPPED|OPEN|CLOSED|DRIFT|LOOP|REDUNDANT|INCONCLUSIVE|MISSING|ABSENT|PRESENT)' \
    . 2>/dev/null \
    | grep -Ei 'R[0-9]{1,2}|P0|gate|verdict|status|result' \
    | tail -1000

section "14. CURRENT REGISTRY / DEPLOYMENT SURFACE"

grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='*.sqlite*' \
    'REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG|docker build|docker push|docker tag|image:' \
    . 2>/dev/null \
    | head -500

section "15. CURRENT GIT HISTORY RELATED TO P/R"

git log --oneline --decorate --all --max-count=120 2>/dev/null \
    | grep -Ei 'p0|r[0-9]{1,2}|gate|audit|provenance|registry|secret|reconcil|stability' \
    | head -120

section "16. RECENT FILE CHANGES RELATED TO P/R"

find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    -printf '%T@ %TY-%Tm-%Td %TH:%TM:%TS %p\n' \
    2>/dev/null \
    | sort -nr \
    | grep -Ei 'p0|r[0-9]{1,2}|gate|audit|provenance|registry|secret|reconcil|stability' \
    | head -200

section "17. SIZE SUMMARY"

printf 'Total files: '
find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    | wc -l

printf 'Shell scripts: '
find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( -name '*.sh' -o -name '*.bash' \) \
    | wc -l

printf 'Log/report files: '
find . -type f \
    -not -path './.git/*' \
    -not -path './.venv/*' \
    -not -path './node_modules/*' \
    \( -iname '*.log' -o -iname '*report*' -o -iname '*result*' \) \
    | wc -l

section "18. COLLECTION END"

echo "OUTPUT_FILE=$OUT"
echo "============================================================"
echo "END P0 → R1-R65 META-AUDIT COLLECTION"
echo "============================================================"
