#!/data/data/com.termux/files/usr/bin/bash

set -u

ROOT="$(pwd)"
TS="$(date '+%Y%m%d_%H%M%S')"
OUT="P0_R54_R65_FRONTIER_ANALYSIS_${TS}.txt"

exec > >(tee "$OUT") 2>&1

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

find_r_files() {
    local n="$1"
    find "$ROOT" -type f \
        ! -path '*/.git/*' \
        ! -path '*/node_modules/*' \
        ! -path '*/.venv/*' \
        ! -path '*/__pycache__/*' \
        -print 2>/dev/null |
    while IFS= read -r f; do
        b="${f##*/}"
        if printf '%s\n' "$b" |
            grep -Eiq "(^|[^a-zA-Z0-9])r0*${n}([^0-9]|$)"; then
            printf '%s\n' "$f"
        fi
    done
}

latest_r_files() {
    local n="$1"
    find_r_files "$n" |
    while IFS= read -r f; do
        stat -c '%Y|%n' "$f" 2>/dev/null || true
    done |
    sort -nr |
    head -5
}

section "0. HEADER"

printf 'DATE=%s\n' "$(date --iso-8601=seconds)"
printf 'ROOT=%s\n' "$ROOT"
printf 'OUTPUT=%s\n' "$OUT"

section "1. GIT STATE"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    printf 'GIT_ROOT=%s\n' "$(git rev-parse --show-toplevel)"
    printf 'BRANCH=%s\n' "$(git branch --show-current 2>/dev/null)"
    printf 'HEAD=%s\n' "$(git rev-parse --short HEAD 2>/dev/null)"

    printf '\n--- STATUS SUMMARY ---\n'
    git status --short 2>/dev/null | head -80

    printf '\n--- RECENT COMMITS ---\n'
    git log -15 --oneline --decorate 2>/dev/null
else
    printf 'GIT=NOT_FOUND\n'
fi

section "2. R54-R65 EXACT FILE DISCOVERY"

for n in $(seq 54 65); do
    printf '\nR%-2s\n' "$n"

    files="$(find_r_files "$n")"

    if [ -z "$files" ]; then
        printf 'STATUS=NOT_FOUND\n'
        continue
    fi

    count="$(printf '%s\n' "$files" | grep -c . || true)"
    printf 'STATUS=PRESENT\n'
    printf 'COUNT=%s\n' "$count"

    latest_r_files "$n"
done

section "3. EXACT R55 CHECK"

printf '%s\n' '--- filenames containing an actual R55 token ---'

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print 2>/dev/null |
while IFS= read -r f; do
    b="${f##*/}"
    if printf '%s\n' "$b" |
        grep -Eiq "(^|[^a-zA-Z0-9])r55([^0-9]|$)"; then
        printf '%s\n' "$f"
    fi
done |
head -80

printf '\n--- textual references to R55 in R56 artifacts ---\n'

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print 2>/dev/null |
while IFS= read -r f; do
    b="${f##*/}"

    if printf '%s\n' "$b" | grep -Eiq 'r56'; then
        grep -nEi '(^|[^a-zA-Z0-9])r55([^0-9]|$)' "$f" 2>/dev/null |
            head -20 |
            sed "s#^#FILE=$f:#"
    fi
done

section "4. R57-R65 DISCOVERY BY CONTENT"

for n in $(seq 57 65); do
    printf '\n--- R%s CONTENT REFERENCES ---\n' "$n"

    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=.venv \
        --exclude-dir=__pycache__ \
        --exclude='*.pyc' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        "(^|[^a-zA-Z0-9])R0*${n}([^0-9]|$)" \
        "$ROOT" 2>/dev/null |
    head -25
done

section "5. R54-R65 DECISION SIGNALS"

for n in $(seq 54 65); do
    printf '\n--- R%s ---\n' "$n"

    files="$(find_r_files "$n")"

    if [ -z "$files" ]; then
        printf 'NO_FILES\n'
        continue
    fi

    found=0

    printf '%s\n' "$files" |
    while IFS= read -r f; do
        signals="$(
            grep -nEi \
                '(^|[^A-Z])(STATUS|RESULT|VERDICT|DECISION|EXIT_CODE|FAILURE_COUNT|BLOCKED|OPEN|CLOSED|PASS|FAIL|REVIEW|PENDING)([^A-Z]|$)' \
                "$f" 2>/dev/null |
            tail -15
        )"

        if [ -n "$signals" ]; then
            printf '\nFILE=%s\n' "$f"
            printf '%s\n' "$signals"
        fi
    done
done

section "6. ACTIVE P0-03 DECISION CHAIN"

for n in $(seq 37 56); do
    files="$(find_r_files "$n")"

    if [ -z "$files" ]; then
        printf 'R%s | NO_FILE\n' "$n"
        continue
    fi

    signal="$(
        printf '%s\n' "$files" |
        while IFS= read -r f; do
            grep -hEi \
                '^[[:space:]]*(P0_03_R[0-9]+_STATUS|RESULT|EXIT_CODE|VERDICT)=' \
                "$f" 2>/dev/null || true
        done |
        tail -4 |
        tr '\n' ' '
    )"

    printf 'R%-2s | %s\n' "$n" "${signal:-NO_DECISION_SIGNAL}"
done

section "7. CURRENT AUTHORITY KEY SURFACE"

for f in \
    "$ROOT/docker-compose.yml" \
    "$ROOT/scripts/deploy.sh" \
    "$ROOT/.env" \
    "$ROOT/.env.production"
do
    [ -f "$f" ] || continue

    printf '\nFILE=%s\n' "$f"

    grep -nEi \
        'REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG|docker compose|docker push|docker pull|image:' \
        "$f" 2>/dev/null |
    sed -E \
        's/(REGISTRY_IMAGE_PREFIX=).*/\1<REDACTED>/;
         s/(RELEASE_ID=).*/\1<REDACTED>/;
         s/(IMAGE_TAG=).*/\1<REDACTED>/'
done

section "8. R60-R65 ACTIVE ARTIFACTS"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print 2>/dev/null |
grep -Ei \
    '(^|[/_.-])(r60|r61|r62|r63|r64|r65)([/_.-]|$)' |
while IFS= read -r f; do
    printf '%s|' "$(stat -c '%Y' "$f" 2>/dev/null || echo 0)"
    printf '%s\n' "$f"
done |
sort -nr |
head -120

section "9. CHRONOLOGICAL FRONTIER"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print 2>/dev/null |
while IFS= read -r f; do
    b="${f##*/}"

    if printf '%s\n' "$b" |
        grep -Eiq '(p0|phase_p0|r[0-9]+|production-release|registry|release|deploy|rollback|recovery)'; then

        ts="$(stat -c '%Y' "$f" 2>/dev/null || echo 0)"
        printf '%s|%s\n' "$ts" "$f"
    fi
done |
sort -nr |
head -100

section "10. REWORK / REPAIR MARKERS"

find "$ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/node_modules/*' \
    ! -path '*/.venv/*' \
    -print 2>/dev/null |
grep -Ei \
    '(broken|\.pre_|fix_|repair|reconcile|regression|recheck|retry|probe|locator|hardening|corrected|supersed|backup)' |
head -150

section "11. DECISION MAP / GLOBAL STATE ARTIFACTS"

find "$ROOT" -maxdepth 1 -type f \
    \( \
        -iname '*DECISION*MAP*.txt' \
        -o -iname 'GLOBAL_P0_R1_R65_STATE*.txt' \
        -o -iname '*META_AUDIT*.txt' \
    \) \
    -print 2>/dev/null |
while IFS= read -r f; do
    printf '%s|' "$(stat -c '%Y' "$f" 2>/dev/null || echo 0)"
    printf '%s\n' "$f"
done |
sort -nr |
head -20

section "12. FINAL MACHINE SUMMARY"

printf 'R54=%s\n' "$(find_r_files 54 | grep -c . || true)"
printf 'R55=%s\n' "$(find_r_files 55 | grep -c . || true)"
printf 'R56=%s\n' "$(find_r_files 56 | grep -c . || true)"
printf 'R57=%s\n' "$(find_r_files 57 | grep -c . || true)"
printf 'R58=%s\n' "$(find_r_files 58 | grep -c . || true)"
printf 'R59=%s\n' "$(find_r_files 59 | grep -c . || true)"
printf 'R60=%s\n' "$(find_r_files 60 | grep -c . || true)"
printf 'R61=%s\n' "$(find_r_files 61 | grep -c . || true)"
printf 'R62=%s\n' "$(find_r_files 62 | grep -c . || true)"
printf 'R63=%s\n' "$(find_r_files 63 | grep -c . || true)"
printf 'R64=%s\n' "$(find_r_files 64 | grep -c . || true)"
printf 'R65=%s\n' "$(find_r_files 65 | grep -c . || true)"

printf '\nOUTPUT_FILE=%s\n' "$OUT"

section "END"
