#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/waste-platform"
cd "$ROOT" || exit 1

TS="$(date '+%Y%m%d_%H%M%S')"
OUT="$ROOT/R60_R65_FORENSIC_RECONCILIATION_${TS}.txt"

exec > >(tee "$OUT") 2>&1

echo "============================================================"
echo "R60 → R65 FORENSIC RECONCILIATION"
echo "============================================================"
echo "DATE=$(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJECT=$ROOT"
echo "MODE=READ_ONLY"
echo "============================================================"

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

find_r_files() {
    local n="$1"
    find "$ROOT" -type f \
        ! -path '*/.git/*' \
        ! -path '*/node_modules/*' \
        ! -path '*/.venv/*' \
        ! -path '*/__pycache__/*' \
        -printf '%T@|%p\n' 2>/dev/null |
    grep -Ei "(^|[/_.-])r0*${n}([_.-]|$)" |
    sort -nr
}

section "1. R60 → R65 ARTIFACT INVENTORY"

for n in 60 61 62 63 64 65; do
    echo
    echo "--- R$n ---"
    files="$(find_r_files "$n" || true)"

    if [ -z "$files" ]; then
        echo "ARTIFACTS=NOT_FOUND"
    else
        echo "$files" | head -12
        count="$(printf '%s\n' "$files" | wc -l | tr -d ' ')"
        echo "ARTIFACT_COUNT=$count"
    fi
done

section "2. R60 DECISION EVIDENCE"

for n in 60; do
    files="$(find_r_files "$n" | cut -d'|' -f2- | head -20 || true)"

    if [ -z "$files" ]; then
        echo "R60_EVIDENCE=NOT_FOUND"
    else
        for f in $files; do
            [ -f "$f" ] || continue
            echo
            echo "--- FILE: ${f#$ROOT/} ---"
            grep -Ein \
              '(STATUS|RESULT|VERDICT|EXIT_CODE|PASS|FAIL|BLOCKED|BLOCKER|OPEN|CLOSED|CLOSURE|FINAL|AUTHORITY|GATE|REGRESSION|SUPERSED|RECONCIL|REMEDIAT|ERROR)' \
              "$f" 2>/dev/null | tail -40
        done
    fi
done

section "3. R61 → R65 DECISION SIGNALS"

for n in 61 62 63 64 65; do
    echo
    echo "--- R$n SIGNALS ---"

    files="$(find_r_files "$n" | cut -d'|' -f2- | head -30 || true)"

    if [ -z "$files" ]; then
        echo "SIGNAL=NOT_FOUND"
        continue
    fi

    found=0

    for f in $files; do
        [ -f "$f" ] || continue

        hits="$(
            grep -Ein \
              '(STATUS|RESULT|VERDICT|EXIT_CODE|PASS|FAIL|BLOCKED|BLOCKER|OPEN|CLOSED|CLOSURE|FINAL|AUTHORITY|GATE|REGRESSION|SUPERSED|RECONCIL|REMEDIAT|ERROR)' \
              "$f" 2>/dev/null | tail -15
        )"

        if [ -n "$hits" ]; then
            echo
            echo "FILE=${f#$ROOT/}"
            printf '%s\n' "$hits"
            found=1
        fi
    done

    [ "$found" -eq 0 ] && echo "DECISION_SIGNALS=NOT_FOUND"
done

section "4. SUPERSESSION / RECONCILIATION CHAIN"

grep -RInE \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=__pycache__ \
  '(R60|R61|R62|R63|R64|R65).*(supersed|replac|reconcil|fix|repair|correct|follow|continu|prior|previous|closure|authority)' \
  "$ROOT" 2>/dev/null |
grep -Ev \
  'P0_R1_R65_MASTER_DECISION_GATE_|P0_R1_R65_GLOBAL_TRUTH_MAP_|P0_R1_R65_CLOSURE_TRUTH_MAP_|P0_R1_R65_DECISION_MAP_|P0_R1_R65_META_AUDIT_' |
head -100

section "5. R60 BLOCKER REFERENCES"

grep -RInE \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=.venv \
  --exclude-dir=__pycache__ \
  '(R60|r60).*(BLOCKER|BLOCKED|FAIL|ERROR|OPEN)' \
  "$ROOT" 2>/dev/null |
head -80

section "6. R62 REGISTRY AUTHORITY SHAPE"

echo "--- docker-compose.yml ---"

if [ -f "$ROOT/docker-compose.yml" ]; then
    grep -nE \
      '(image:|REGISTRY_IMAGE_PREFIX|IMAGE_TAG|RELEASE_ID)' \
      "$ROOT/docker-compose.yml" 2>/dev/null |
    sed -E \
      's/(REGISTRY_IMAGE_PREFIX=).*/\1<REDACTED>/g;
       s/(IMAGE_TAG=).*/\1<REDACTED>/g;
       s/(RELEASE_ID=).*/\1<REDACTED>/g'
else
    echo "docker-compose.yml=NOT_FOUND"
fi

echo
echo "--- ENVIRONMENT KEY PRESENCE ONLY ---"

for k in REGISTRY_IMAGE_PREFIX IMAGE_TAG RELEASE_ID; do
    if [ -n "${!k:-}" ]; then
        echo "$k=PRESENT"
    else
        echo "$k=ABSENT"
    fi
done

section "7. CURRENT MASTER GATE"

MASTER="$(find "$HOME" -maxdepth 1 -type f \
    -name 'P0_R1_R65_MASTER_DECISION_GATE_*.txt' \
    -printf '%T@|%p\n' 2>/dev/null | sort -nr | head -1 | cut -d'|' -f2-)"

if [ -n "${MASTER:-}" ] && [ -f "$MASTER" ]; then
    echo "MASTER=$(basename "$MASTER")"

    grep -nE \
      '^(FACT_|DECISION_MAP=|META_AUDIT=|DO NOT CONTINUE|AUTHORIZED_NEXT_STEP|A =|B =|C =|D =|E =|F =|OUTPUT_|END )' \
      "$MASTER" 2>/dev/null |
    tail -80
else
    echo "MASTER=NOT_FOUND"
fi

section "8. LATEST R60 → R65 FILE CHRONOLOGY"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%p\n' 2>/dev/null |
grep -Ei \
  'r(60|61|62|63|64|65)([^0-9]|$)|R(60|61|62|63|64|65)([^0-9]|$)' |
sort -nr |
head -80

section "9. GIT STATE"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "--- BRANCH ---"
    git branch --show-current 2>/dev/null || true

    echo
    echo "--- STATUS (MAX 80) ---"
    git status --short 2>/dev/null | head -80

    echo
    echo "--- RECENT COMMITS ---"
    git log -12 --oneline --decorate 2>/dev/null || true
else
    echo "GIT=NOT_A_REPOSITORY"
fi

section "10. FINAL MACHINE SUMMARY"

for n in 60 61 62 63 64 65; do
    files="$(find_r_files "$n" || true)"

    if [ -z "$files" ]; then
        echo "R$n=NOT_FOUND"
    else
        count="$(printf '%s\n' "$files" | wc -l | tr -d ' ')"
        latest="$(printf '%s\n' "$files" | head -1 | cut -d'|' -f2-)"
        echo "R$n=PRESENT|COUNT=$count|LATEST=${latest#$ROOT/}"
    fi
done

echo
echo "============================================================"
echo "END R60 → R65 FORENSIC RECONCILIATION"
echo "============================================================"
echo "OUTPUT_FILE=$OUT"
echo "OUTPUT_LINES=$(wc -l < "$OUT" | tr -d ' ')"
echo "MODE=READ_ONLY"
echo "============================================================"
