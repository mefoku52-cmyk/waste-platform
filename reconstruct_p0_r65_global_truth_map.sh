#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$PWD"
TS="$(date '+%Y%m%d_%H%M%S')"
OUT="P0_R1_R65_GLOBAL_TRUTH_MAP_${TS}.txt"

exec > >(tee "$OUT") 2>&1

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

redact() {
    sed -E \
        -e 's/(TELEGRAM_BOT_TOKEN|DEV_PASSWORD_HASH|SECRET_KEY|DATABASE_URL|PASSWORD|TOKEN|API_KEY|ACCESS_KEY|PRIVATE_KEY|REGISTRY_PASSWORD)=([^[:space:]]+)/\1=<REDACTED>/Ig' \
        -e 's/(REGISTRY_IMAGE_PREFIX)=([^[:space:]]+)/\1=<VALUE_PRESENT>/Ig' \
        -e 's/(RELEASE_ID)=([^[:space:]]+)/\1=<VALUE_PRESENT>/Ig' \
        -e 's/(IMAGE_TAG)=([^[:space:]]+)/\1=<VALUE_PRESENT>/Ig'
}

latest_decision_map() {
    find "$ROOT" -type f \
        -name 'P0_R1_R65_DECISION_MAP_*.txt' \
        -print 2>/dev/null |
        sort |
        tail -1
}

latest_meta_audit() {
    find "$ROOT" -type f \
        -name 'P0_R1_R65_META_AUDIT_*.txt' \
        -print 2>/dev/null |
        sort |
        tail -1
}

section "0. GLOBAL RECONSTRUCTION HEADER"

printf 'DATE=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
printf 'PROJECT=%s\n' "$ROOT"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    printf 'GIT_ROOT=%s\n' "$(git rev-parse --show-toplevel)"
    printf 'GIT_BRANCH=%s\n' "$(git branch --show-current 2>/dev/null || true)"
    printf 'GIT_HEAD=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || true)"
else
    printf 'GIT=NOT_A_REPOSITORY\n'
fi

section "1. EXISTING MASTER MAPS"

DECISION="$(latest_decision_map)"
META="$(latest_meta_audit)"

printf 'LATEST_DECISION_MAP=%s\n' "${DECISION:-NOT_FOUND}"
printf 'LATEST_META_AUDIT=%s\n' "${META:-NOT_FOUND}"

if [ -n "${DECISION:-}" ] && [ -f "$DECISION" ]; then
    printf '\n--- DECISION SIGNALS ---\n'
    grep -E '^[[:space:]]*R[0-9]+:' "$DECISION" 2>/dev/null |
        tail -80
fi

section "2. CURRENT R1-R65 ARTIFACT MATRIX"

printf '%-5s %-8s %-8s %-8s %s\n' \
    "R" "FILES" "REPORTS" "SCRIPTS" "LATEST_ARTIFACT"

for N in $(seq 1 65); do
    PATTERN="(^|[/_.-])r0*${N}([_.-]|$)"

    FILES="$(
        find "$ROOT" -type f \
            -not -path '*/.git/*' \
            -not -path '*/node_modules/*' \
            -print 2>/dev/null |
        grep -Ei "$PATTERN" || true
    )"

    COUNT="$(printf '%s\n' "$FILES" | sed '/^$/d' | wc -l | tr -d ' ')"
    REPORTS="$(printf '%s\n' "$FILES" |
        grep -Ei '\.(txt|log|md)$' |
        wc -l | tr -d ' ')"
    SCRIPTS="$(printf '%s\n' "$FILES" |
        grep -Ei '\.(sh|bash)$' |
        wc -l | tr -d ' ')"

    LATEST="$(
        printf '%s\n' "$FILES" |
        while IFS= read -r F; do
            [ -f "$F" ] || continue
            printf '%s|%s\n' "$(stat -c '%Y' "$F" 2>/dev/null || echo 0)" "$F"
        done |
        sort -nr |
        head -1 |
        cut -d'|' -f2-
    )"

    [ -n "$LATEST" ] || LATEST="NONE"

    printf '%-5s %-8s %-8s %-8s %s\n' \
        "R$N" "$COUNT" "$REPORTS" "$SCRIPTS" "$LATEST"
done

section "3. EXECUTION / DECISION SIGNALS PER R"

for N in $(seq 1 65); do
    PATTERN="(^|[/_.-])r0*${N}([_.-]|$)"

    FILES="$(
        find "$ROOT" -type f \
            -not -path '*/.git/*' \
            -not -path '*/node_modules/*' \
            -print 2>/dev/null |
        grep -Ei "$PATTERN" || true
    )"

    if [ -z "$FILES" ]; then
        printf 'R%-2s | NOT_FOUND | no matching artifact\n' "$N"
        continue
    fi

    SIGNALS="$(
        printf '%s\n' "$FILES" |
        while IFS= read -r F; do
            [ -f "$F" ] || continue
            grep -HinE \
                '(^|[^A-Z])(STATUS|RESULT|VERDICT|OUTCOME|EXIT_CODE|DECISION|FINAL|CLOSED|OPEN_REVIEW|INCOMPLETE|PASS|FAIL|ERROR|BLOCKED|REVIEW|SUPERSEDED)[[:space:]]*=' \
                "$F" 2>/dev/null |
                redact || true
        done |
        tail -8
    )"

    if [ -n "$SIGNALS" ]; then
        printf '\nR%-2s | SIGNALS\n' "$N"
        printf '%s\n' "$SIGNALS"
    else
        printf 'R%-2s | PRESENT | no explicit terminal signal found\n' "$N"
    fi
done

section "4. REWORK / LOOP / RECONCILIATION DETECTION"

printf '%s\n' 'Files suggesting repair, parser churn, repeated verification, or supersession:'

find "$ROOT" -type f \
    -not -path '*/.git/*' \
    -not -path '*/node_modules/*' \
    -print 2>/dev/null |
grep -Ei \
    '(r[0-9]+).*(broken|fix|repair|pre_|post_|recheck|retry|retry|regression|reconcile|reconciliation|supersed|final|closure|hardening|correct|probe|stability|deterministic|semantic)' |
sort |
tail -180

section "5. P0 PHASE RECONSTRUCTION"

printf '%s\n' 'P0.01:'
find "$ROOT" -type f -print 2>/dev/null |
grep -Ei '(^|[/_.-])p0[_-]?0?1|phase_p0_01' |
sort |
tail -80

printf '\nP0.02:\n'
find "$ROOT" -type f -print 2>/dev/null |
grep -Ei '(^|[/_.-])p0[_-]?0?2|phase_p0_02' |
sort |
tail -120

printf '\nP0.03:\n'
find "$ROOT" -type f -print 2>/dev/null |
grep -Ei '(^|[/_.-])p0[_-]?0?3|phase_p0_03' |
sort |
tail -120

section "6. CHRONOLOGICAL LAST 120 RELEVANT ARTIFACTS"

find "$ROOT" -type f \
    -not -path '*/.git/*' \
    -not -path '*/node_modules/*' \
    -print 2>/dev/null |
grep -Ei \
    '(^|/)(phase_p0|p0[_-].*r[0-9]+|.*r[0-9]+.*(gate|proof|closure|audit|reconciliation|authority|readiness)).*' |
while IFS= read -r F; do
    [ -f "$F" ] || continue
    printf '%s|%s\n' \
        "$(stat -c '%Y' "$F" 2>/dev/null || echo 0)" \
        "$F"
done |
sort -nr |
head -120 |
while IFS='|' read -r EPOCH F; do
    [ -n "$F" ] || continue
    printf '%s | %s\n' \
        "$(date -d "@$EPOCH" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || printf '%s' "$EPOCH")" \
        "$F"
done

section "7. EXPLICIT R57-R65 GAP CHECK"

for N in 57 58 59 60 61 62 63 64 65; do
    echo
    printf '%s\n' "--- R$N ---"

    find "$ROOT" -type f \
        -not -path '*/.git/*' \
        -not -path '*/node_modules/*' \
        -print 2>/dev/null |
    grep -Ei "(^|[/_.-])r0*${N}([_.-]|$)" |
    sort |
    tail -40 || true
done

section "8. R62 REGISTRY AUTHORITY SHAPE, KEY PRESENCE ONLY"

for F in \
    "$ROOT/docker-compose.yml" \
    "$ROOT/compose.yml" \
    "$ROOT/.env.example" \
    "$ROOT/.github/workflows"/*.yml \
    "$ROOT/.github/workflows"/*.yaml
do
    [ -f "$F" ] || continue

    printf '\nFILE=%s\n' "$F"

    grep -nEi \
        'REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG|image:[[:space:]]|docker build|docker push' \
        "$F" 2>/dev/null |
    redact |
    head -80
done

section "9. GIT STATE, WITHOUT CONTENT DUMP"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    printf '%s\n' '--- STATUS ---'
    git status --short 2>/dev/null | head -100

    printf '\n%s\n' '--- RECENT COMMITS ---'
    git log -20 --oneline --decorate 2>/dev/null

    printf '\n%s\n' '--- BRANCHES ---'
    git branch -a 2>/dev/null | head -80
else
    printf '%s\n' 'GIT_NOT_AVAILABLE'
fi

section "10. STALE-MAP TEST"

printf 'Current relevant artifacts newer than latest decision map:\n'

if [ -n "${DECISION:-}" ] && [ -f "$DECISION" ]; then
    MAP_EPOCH="$(stat -c '%Y' "$DECISION" 2>/dev/null || echo 0)"

    find "$ROOT" -type f \
        -not -path '*/.git/*' \
        -not -path '*/node_modules/*' \
        -newermt "@$(date -d "@$MAP_EPOCH" '+%Y-%m-%d %H:%M:%S')" \
        -print 2>/dev/null |
    grep -Ei \
        '(^|/)(phase_p0|p0[_-].*r[0-9]+|.*r[0-9]+.*(gate|proof|closure|audit|reconciliation|authority|readiness))' |
    sort |
    tail -100 || true
else
    printf '%s\n' 'DECISION_MAP_NOT_FOUND'
fi

section "11. PRELIMINARY MACHINE CLASSIFICATION"

for N in $(seq 1 65); do
    PATTERN="(^|[/_.-])r0*${N}([_.-]|$)"

    FILES="$(
        find "$ROOT" -type f \
            -not -path '*/.git/*' \
            -not -path '*/node_modules/*' \
            -print 2>/dev/null |
        grep -Ei "$PATTERN" || true
    )"

    if [ -z "$FILES" ]; then
        printf 'R%-2s | NOT_FOUND\n' "$N"
        continue
    fi

    TEXT="$(
        printf '%s\n' "$FILES" |
        while IFS= read -r F; do
            [ -f "$F" ] || continue
            grep -hiE \
                '(^|[^A-Z])(STATUS|RESULT|VERDICT|OUTCOME|DECISION|CLOSED|OPEN_REVIEW|INCOMPLETE|PASS|FAIL|ERROR|BLOCKED|REVIEW|SUPERSEDED)[[:space:]]*=' \
                "$F" 2>/dev/null |
            redact || true
        done
    )"

    if printf '%s\n' "$TEXT" | grep -qiE 'OPEN_REVIEW|INCOMPLETE|BLOCKED|ERROR|FAIL'; then
        CLASS="OPEN_REVIEW"
    elif printf '%s\n' "$TEXT" | grep -qiE 'SUPERSEDED'; then
        CLASS="SUPERSEDED_REVIEW"
    elif printf '%s\n' "$TEXT" | grep -qiE 'CLOSED|PASS|SUCCESS'; then
        CLASS="CANDIDATE_DONE"
    else
        CLASS="PRESENT_UNPROVEN"
    fi

    printf 'R%-2s | %s\n' "$N" "$CLASS"
done

section "12. FINAL RECONSTRUCTION RULE"

cat <<'RULE'
Toto nie je remediation.
Toto nie je nový R-krok.
Toto je read-only rekonštrukcia dôkazového reťazca.

PRESENT != CLOSED
FILE EXISTS != EXECUTION PROVED
PASS != FINAL AUTHORITY
LATEST FILE != LATEST VALID DECISION

Definitívna klasifikácia sa vykoná až po analytickom prečítaní tohto snapshotu.
RULE

printf '\nOUTPUT=%s\n' "$OUT"
