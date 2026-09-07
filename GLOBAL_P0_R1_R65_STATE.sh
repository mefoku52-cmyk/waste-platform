#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$PWD"
TS="$(date '+%Y%m%d_%H%M%S')"
OUT="GLOBAL_P0_R1_R65_STATE_${TS}.txt"

exec > >(tee "$OUT") 2>&1

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

# ------------------------------------------------------------
# ONLY ACTIVE / AUTHORITATIVE SURFACES
# ------------------------------------------------------------
EXCLUDES='
./.git
./.next
./node_modules
./_quarantine
./scripts/forensics/archive
./audit-output
./P0_R1_R65_META_AUDIT_*
./P0_R1_R65_DECISION_MAP_*
'

is_excluded() {
    case "$1" in
        ./.git/*|./.next/*|./node_modules/*|./_quarantine/*|\
        ./scripts/forensics/archive/*|./audit-output/*|\
        ./P0_R1_R65_META_AUDIT_*|./P0_R1_R65_DECISION_MAP_*)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

active_files() {
    find . -type f \
        ! -path './.git/*' \
        ! -path './.next/*' \
        ! -path './node_modules/*' \
        ! -path './_quarantine/*' \
        ! -path './scripts/forensics/archive/*' \
        ! -path './audit-output/*' \
        ! -name 'P0_R1_R65_META_AUDIT_*' \
        ! -name 'P0_R1_R65_DECISION_MAP_*' \
        -print
}

section "0. IDENTITY"
printf 'DATE=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
printf 'ROOT=%s\n' "$ROOT"
printf 'HOST=%s\n' "$(hostname 2>/dev/null || true)"
printf 'USER=%s\n' "${USER:-unknown}"

section "1. GIT STATE"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    printf 'GIT_ROOT=%s\n' "$(git rev-parse --show-toplevel)"
    printf 'BRANCH=%s\n' "$(git branch --show-current 2>/dev/null || true)"
    printf 'HEAD=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || true)"
    printf '\n-- STATUS --\n'
    git status --short 2>/dev/null | head -60
    printf '\n-- LAST COMMITS --\n'
    git log -12 --oneline --decorate 2>/dev/null
else
    printf 'GIT=NOT_AVAILABLE\n'
fi

section "2. ACTIVE P0/R FILE INVENTORY"
active_files | grep -Ei \
    '(^|[/_.-])(phase_)?p0([_-][0-9]+)?|(^|[/_.-])r[0-9]{1,2}([_.-]|$)' \
    | grep -Ei '\.(sh|txt|log|md)$' \
    | sort \
    | tail -180

section "3. R1-R65 ACTIVE MATRIX"
for N in $(seq 1 65); do
    PATTERN="(^|[/_.-])r0*${N}([_.-]|$)"
    FILES="$(
        active_files |
        grep -Ei "$PATTERN" |
        grep -Ei '\.(sh|txt|log)$' |
        sort -V 2>/dev/null |
        tail -20
    )"

    COUNT=0
    [ -n "$FILES" ] && COUNT="$(printf '%s\n' "$FILES" | sed '/^$/d' | wc -l | tr -d ' ')"

    if [ "$COUNT" -gt 0 ]; then
        LAST="$(printf '%s\n' "$FILES" | tail -1)"
        printf 'R%-2s | PRESENT | %s | %s\n' "$N" "$COUNT" "$LAST"
    else
        printf 'R%-2s | NOT_FOUND\n' "$N"
    fi
done

section "4. ACTIVE REPORT DECISIONS ONLY"
active_files |
    grep -Ei '\.(txt|log)$' |
    grep -Ei '(p0[_-].*r[0-9]+|phase_p0.*r[0-9]+|r[0-9]+.*(gate|proof|closure|audit|verification|reconciliation))' |
    while IFS= read -r F; do
        SIG="$(
            grep -Ehi \
            '^[[:space:]]*(P0_[A-Z0-9_-]*STATUS|STATUS|RESULT|VERDICT|DECISION|EXIT_CODE|NEXT_STAGE|BLOCKER|CURRENT_BLOCKER|FAILURE_COUNT|REVIEW_REQUIRED)[[:space:]]*=' \
            "$F" 2>/dev/null |
            tail -8
        )"

        if [ -n "$SIG" ]; then
            printf '\nFILE=%s\n' "$F"
            printf '%s\n' "$SIG"
        fi
    done |
    head -220

section "5. RECENT ACTIVE P0/R TIMELINE"
active_files |
    grep -Ei '(phase_p0|p0_[0-9]+_r[0-9]+|p0-[0-9]+.*r[0-9]+)' |
    while IFS= read -r F; do
        MT="$(stat -c '%Y' "$F" 2>/dev/null || echo 0)"
        printf '%s|%s\n' "$MT" "$F"
    done |
    sort -nr |
    head -100

section "6. REWORK / LOOP SIGNALS IN ACTIVE TREE"
active_files |
    grep -Ei \
    '(broken|fix|fixed|repair|remed|v[0-9]+|retry|recheck|reconcile|regression|post-r|final|closure|probe|locator|classifier)' |
    grep -Ei '(p0|r[0-9]+)' |
    tail -120

section "7. P0 PHASE DISTRIBUTION"
for P in P0-01 P0-02 P0-03 p0_01 p0_02 p0_03; do
    C="$(
        active_files |
        grep -Ei "$P" |
        wc -l |
        tr -d ' '
    )"
    printf '%-8s %s\n' "$P" "$C"
done

section "8. CURRENT REGISTRY / RELEASE AUTHORITY SHAPE"
for F in \
    docker-compose.yml \
    deploy-production.sh \
    deploy.sh \
    scripts/deploy.sh \
    .github/workflows/deploy.yml
do
    if [ -f "$F" ]; then
        printf '\nFILE=%s\n' "$F"
        grep -nEi \
        'REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG|image:|docker build|docker push|docker pull|docker compose|deploy' \
        "$F" 2>/dev/null |
        sed -E \
        's/(REGISTRY_IMAGE_PREFIX=).*/\1<REDACTED>/;
         s/(RELEASE_ID=).*/\1<REDACTED>/;
         s/(IMAGE_TAG=).*/\1<REDACTED>/;
         s/(TOKEN=).*/\1<REDACTED>/;
         s/(PASSWORD=).*/\1<REDACTED>/;
         s/(SECRET=).*/\1<REDACTED>/'
    fi
done

section "9. ENV KEY PRESENCE ONLY"
for F in .env .env.production .env.prod; do
    if [ -f "$F" ]; then
        printf 'FILE=%s\n' "$F"
        grep -E '^[[:space:]]*(REGISTRY_IMAGE_PREFIX|RELEASE_ID|IMAGE_TAG)[[:space:]]*=' "$F" 2>/dev/null |
        sed -E 's/=.*$/=<VALUE_PRESENT>/'
    fi
done

printf '\n'
printf '============================================================\n'
printf 'END GLOBAL P0/R1-R65 STATE\n'
printf 'OUTPUT=%s\n' "$OUT"
printf '============================================================\n'
