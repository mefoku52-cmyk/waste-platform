#!/usr/bin/env bash
set -u

OUT="P0_R1_R65_DECISION_MAP_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "P0 → R1-R65 DECISION MAP"
echo "============================================================"
echo "DATE=$(date -Is)"
echo "PROJECT=$(pwd)"
echo

echo "============================================================"
echo "1. P0 / R FILES CHRONOLOGICAL"
echo "============================================================"

find . -type f \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%p\n' \
  2>/dev/null |
sort -n |
grep -Ei \
  'p0|r[0-9]{1,2}|phase.*(p0|r[0-9])|gate|provenance|reconcil|authority|stability|registry|secret' |
tail -600

echo
echo "============================================================"
echo "2. GATE TITLES ONLY"
echo "============================================================"

grep -RInE \
  --include='*.sh' \
  --include='*.bash' \
  --include='*.txt' \
  --include='*.md' \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  '(P0-[0-9]+|P0_[0-9]+|R[0-9]{1,2})[[:space:]_-]+[A-Za-z][A-Za-z0-9 _:-]{3,160}' \
  . 2>/dev/null |
sed -E 's/^([^:]+:[0-9]+:)/\1 /' |
head -1500

echo
echo "============================================================"
echo "3. STATUS / RESULT / VERDICT / EXIT"
echo "============================================================"

grep -RInE \
  --include='*.sh' \
  --include='*.bash' \
  --include='*.txt' \
  --include='*.log' \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  '(STATUS|RESULT|VERDICT|EXIT_CODE|REPORT)[[:space:]]*=' \
  . 2>/dev/null |
grep -Ei 'P0|R[0-9]{1,2}|gate|phase|audit|proof|provenance|authority|registry|secret' |
head -1800

echo
echo "============================================================"
echo "4. HUMAN VERDICT SIGNALS"
echo "============================================================"

grep -RInE \
  --include='*.sh' \
  --include='*.bash' \
  --include='*.txt' \
  --include='*.log' \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  '\b(PASS|FAIL|FAILED|SUCCESS|ERROR|BLOCKED|SKIPPED|OPEN|CLOSED|INCONCLUSIVE|DRIFT|LOOP|REDUNDANT|MISSING|ABSENT|PRESENT)\b' \
  . 2>/dev/null |
grep -Ei 'P0|R[0-9]{1,2}|gate|phase|audit|proof|provenance|authority|registry|secret' |
head -1800

echo
echo "============================================================"
echo "5. R REFERENCE GRAPH"
echo "============================================================"

grep -RInE \
  --include='*.sh' \
  --include='*.bash' \
  --include='*.txt' \
  --include='*.md' \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  'R[0-9]{1,2}.*R[0-9]{1,2}' \
  . 2>/dev/null |
head -1200

echo
echo "============================================================"
echo "6. P0 REFERENCE GRAPH"
echo "============================================================"

grep -RInE \
  --include='*.sh' \
  --include='*.bash' \
  --include='*.txt' \
  --include='*.md' \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=node_modules \
  'P0-[0-9]+|P0_[0-9]+' \
  . 2>/dev/null |
head -1200

echo
echo "============================================================"
echo "7. DUPLICATE / REPEATED GATE NAMES"
echo "============================================================"

find . -type f \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -printf '%p\n' 2>/dev/null |
grep -Ei 'p0|r[0-9]{1,2}' |
sed -E 's#.*/##' |
sed -E 's/\.(sh|bash|txt|md|log)$//' |
sort |
uniq -c |
sort -nr |
head -300

echo
echo "============================================================"
echo "8. R1-R65 PRESENCE"
echo "============================================================"

for n in $(seq 1 65); do
    matches=$(
        find . -type f \
          -not -path './.git/*' \
          -not -path './.venv/*' \
          -not -path './node_modules/*' \
          -printf '%p\n' 2>/dev/null |
        grep -Ei "(^|[/_.-])r0*${n}([_.-]|[/]|$)" |
        head -10
    )

    if [ -n "$matches" ]; then
        echo "R${n}: PRESENT"
        echo "$matches" | sed 's/^/    /'
    else
        echo "R${n}: NOT_FOUND"
    fi
done

echo
echo "============================================================"
echo "9. P0-01 / P0-02 / OTHER P0 BRANCHES"
echo "============================================================"

find . -type f \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './node_modules/*' \
  -printf '%p\n' 2>/dev/null |
grep -Ei 'p0[_-][0-9]+' |
sed -E 's/.*(p0[_-][0-9]+).*/\1/i' |
sort -fu |
uniq -c

echo
echo "============================================================"
echo "10. RECENT P/R GIT HISTORY"
echo "============================================================"

git log --all \
  --date=iso \
  --pretty=format:'%h|%ad|%s' \
  --max-count=300 2>/dev/null |
grep -Ei 'p0|r[0-9]{1,2}|gate|audit|proof|provenance|authority|registry|secret|reconcil|stability' |
head -300

echo
echo "============================================================"
echo "11. CURRENT ACTIVE THREAD"
echo "============================================================"

find . -maxdepth 1 -type f \
  -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%f\n' \
  2>/dev/null |
sort -nr |
head -80

echo
echo "============================================================"
echo "12. END"
echo "============================================================"
echo "OUTPUT_FILE=$OUT"
echo "============================================================"

} | tee "$OUT"

echo
echo "============================================================"
echo "DECISION MAP CREATED"
echo "============================================================"
echo "FILE=$OUT"
echo "LINES=$(wc -l < "$OUT")"
echo
echo "Pošli mi teraz:"
echo "  head -80 $OUT"
echo "  grep -nE '^(R|P0|STATUS|RESULT|VERDICT|EXIT_CODE|PASS|FAIL|BLOCKED|OPEN|CLOSED)' $OUT | head -250"
echo "============================================================"
