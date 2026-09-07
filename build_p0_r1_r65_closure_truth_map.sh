#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

PROJECT="${HOME}/waste-platform"
cd "$PROJECT" || exit 1

TS="$(date '+%Y%m%d_%H%M%S')"
OUT="${PROJECT}/P0_R1_R65_CLOSURE_TRUTH_MAP_${TS}.txt"
WORK="${PROJECT}/.closure_truth_${TS}"
mkdir -p "$WORK"

# ------------------------------------------------------------
# READ-ONLY
# ------------------------------------------------------------

exec > >(tee -a "$OUT") 2>&1

echo
echo "============================================================"
echo "P0 → R1-R65 CLOSURE TRUTH MAP"
echo "============================================================"
echo "DATE=$(date '+%Y-%m-%dT%H:%M:%S%z')"
echo "PROJECT=$PROJECT"
echo "MODE=READ_ONLY"
echo "OUTPUT=$OUT"
echo "============================================================"
echo

log() {
    printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

section() {
    echo
    echo "------------------------------------------------------------"
    echo "$1"
    echo "------------------------------------------------------------"
}

# ------------------------------------------------------------
# SAFETY
# ------------------------------------------------------------

section "0. READ-ONLY SAFETY"

echo "No files will be modified."
echo "No scripts from the project will be executed."
echo "No .env values will be printed."
echo "No secret values will be printed."
echo

# ------------------------------------------------------------
# BASIC PROJECT STATE
# ------------------------------------------------------------

section "1. PROJECT STATE"

printf 'PWD='
pwd

printf 'GIT_BRANCH='
git branch --show-current 2>/dev/null || true

printf 'GIT_STATUS_SUMMARY='
git status --short 2>/dev/null | wc -l || true

printf 'PROJECT_FILES='
find "$PROJECT" \
    -path "$PROJECT/.git" -prune -o \
    -path "$PROJECT/.venv" -prune -o \
    -path "$PROJECT/node_modules" -prune -o \
    -type f -print 2>/dev/null | wc -l

printf 'SHELL_SCRIPTS='
find "$PROJECT" \
    -path "$PROJECT/.git" -prune -o \
    -path "$PROJECT/.venv" -prune -o \
    -path "$PROJECT/node_modules" -prune -o \
    -type f \( -name '*.sh' -o -perm -111 \) -print 2>/dev/null | wc -l

echo

# ------------------------------------------------------------
# BUILD COMPLETE FILE INDEX
# ------------------------------------------------------------

section "2. BUILDING FORENSIC FILE INDEX"

log "Indexing project files..."

find "$PROJECT" \
    -path "$PROJECT/.git" -prune -o \
    -path "$PROJECT/.venv" -prune -o \
    -path "$PROJECT/node_modules" -prune -o \
    -path "$PROJECT/.closure_truth_${TS}" -prune -o \
    -type f -print0 2>/dev/null \
    > "$WORK/all_files.null"

tr '\0' '\n' < "$WORK/all_files.null" > "$WORK/all_files.txt"

TOTAL_FILES="$(wc -l < "$WORK/all_files.txt")"
log "Indexed $TOTAL_FILES files."

# ------------------------------------------------------------
# REPORT / LOG CANDIDATE INDEX
# ------------------------------------------------------------

section "3. BUILDING REPORT / LOG INDEX"

log "Locating reports, logs and evidence artifacts..."

grep -Ei \
    '(^|/)(.*(report|result|status|audit|gate|closure|verification|proof|reconciliation|ledger|readiness|forensic|output|execution|attestation|integrity|classification|locator|decision|truth).*)$|(\.log$)|(\.txt$)' \
    "$WORK/all_files.txt" \
    > "$WORK/report_candidates.txt" 2>/dev/null || true

log "Report/evidence candidates: $(wc -l < "$WORK/report_candidates.txt")"

# ------------------------------------------------------------
# FUNCTION: BOUNDARY R MATCH
# ------------------------------------------------------------

r_pattern() {
    local n="$1"
    printf '(^|[^[:alnum:]_])r%s([^[:alnum:]_]|$)' "$n"
}

# ------------------------------------------------------------
# FUNCTION: GET FILE MTIME
# ------------------------------------------------------------

file_epoch() {
    stat -c '%Y' "$1" 2>/dev/null || echo 0
}

file_time() {
    local e
    e="$(file_epoch "$1")"
    if [ "$e" -gt 0 ] 2>/dev/null; then
        date -d "@$e" '+%Y-%m-%d %H:%M:%S %z' 2>/dev/null || echo "UNKNOWN"
    else
        echo "UNKNOWN"
    fi
}

# ------------------------------------------------------------
# FUNCTION: SAFE CONTENT SEARCH
# ------------------------------------------------------------

safe_grep_file() {
    local pattern="$1"
    local file="$2"

    # Never inspect .env values.
    case "$file" in
        */.env|*/.env.*|*/secrets/*|*/secret/*)
            return 0
            ;;
    esac

    grep -Eis "$pattern" "$file" 2>/dev/null || true
}

# ------------------------------------------------------------
# PROCESS EACH R
# ------------------------------------------------------------

declare -A FIRST_EXEC
declare -A LAST_EXEC
declare -A LATEST_REPORT
declare -A LATEST_STATUS
declare -A LATEST_RESULT
declare -A LATEST_EXIT
declare -A SUPERSEDES
declare -A SUPERSEDED_BY
declare -A DEPENDENCIES
declare -A OPEN_REVIEW
declare -A FINAL_AUTHORITY
declare -A STATE
declare -A FILE_COUNT
declare -A REPORT_COUNT
declare -A REWORK
declare -A CONFLICT
declare -A FIRST_EPOCH
declare -A LAST_EPOCH

for n in $(seq 1 65); do
    FIRST_EXEC[$n]="NOT_FOUND"
    LAST_EXEC[$n]="NOT_FOUND"
    LATEST_REPORT[$n]="NOT_FOUND"
    LATEST_STATUS[$n]="UNKNOWN"
    LATEST_RESULT[$n]="UNKNOWN"
    LATEST_EXIT[$n]="UNKNOWN"
    SUPERSEDES[$n]="NONE_DETECTED"
    SUPERSEDED_BY[$n]="NONE_DETECTED"
    DEPENDENCIES[$n]="NONE_DETECTED"
    OPEN_REVIEW[$n]="NO"
    FINAL_AUTHORITY[$n]="NO_EVIDENCE"
    STATE[$n]="NOT_FOUND"
    FILE_COUNT[$n]=0
    REPORT_COUNT[$n]=0
    REWORK[$n]="NO"
    CONFLICT[$n]="NO"
    FIRST_EPOCH[$n]=0
    LAST_EPOCH[$n]=0
done

section "4. R1-R65 DISCOVERY"

for n in $(seq 1 65); do

    printf '\n'
    printf '### R%-2s\n' "$n"

    PATTERN="$(r_pattern "$n")"

    # Candidate files with boundary-aware R number.
    : > "$WORK/r${n}_files.txt"

    while IFS= read -r f; do
        case "$f" in
            */.env|*/.env.*|*/secrets/*|*/secret/*)
                continue
                ;;
        esac

        base="$(basename "$f")"

        if printf '%s\n' "$base" | grep -Eiq "$PATTERN"; then
            printf '%s\n' "$f" >> "$WORK/r${n}_files.txt"
            continue
        fi

        # Also inspect textual content for explicit R references.
        if [ -f "$f" ]; then
            size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
            if [ "$size" -le 2000000 ] 2>/dev/null; then
                if grep -Eiq "$PATTERN" "$f" 2>/dev/null; then
                    printf '%s\n' "$f" >> "$WORK/r${n}_files.txt"
                fi
            fi
        fi
    done < "$WORK/all_files.txt"

    # Unique
    sort -u "$WORK/r${n}_files.txt" -o "$WORK/r${n}_files.txt"

    FC="$(wc -l < "$WORK/r${n}_files.txt")"
    FILE_COUNT[$n]="$FC"

    echo "FILES=$FC"

    if [ "$FC" -eq 0 ]; then
        echo "DISCOVERY=NOT_FOUND"
        continue
    fi

    # --------------------------------------------------------
    # REPORT CANDIDATES FOR THIS R
    # --------------------------------------------------------

    : > "$WORK/r${n}_reports.txt"

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        base="$(basename "$f" | tr '[:upper:]' '[:lower:]')"

        is_report=0

        case "$base" in
            *.txt|*.log|*report*|*result*|*status*|*audit*|*gate*|*closure*|*verification*|*proof*|*reconciliation*|*ledger*|*readiness*|*forensic*|*output*|*execution*|*attestation*|*integrity*|*classification*|*locator*|*decision*|*truth*)
                is_report=1
                ;;
        esac

        if [ "$is_report" -eq 0 ]; then
            if grep -Eiq '(^|[^A-Z_])(STATUS|RESULT|EXIT_CODE|PASS|FAIL|REVIEW|CLOSED|OPEN|BLOCKED)[^A-Z_]*=' "$f" 2>/dev/null; then
                is_report=1
            fi
        fi

        if [ "$is_report" -eq 1 ]; then
            printf '%s\n' "$f" >> "$WORK/r${n}_reports.txt"
        fi

    done < "$WORK/r${n}_files.txt"

    sort -u "$WORK/r${n}_reports.txt" -o "$WORK/r${n}_reports.txt"

    RC="$(wc -l < "$WORK/r${n}_reports.txt")"
    REPORT_COUNT[$n]="$RC"

    echo "REPORTS=$RC"

    # --------------------------------------------------------
    # REWORK / VERSION SIGNALS
    # --------------------------------------------------------

    if grep -Eiq \
        '(^|/|_)(broken|fix|fixed|repair|rework|retry|retry[0-9]*|v[0-9]+|variant|pre_|post_|regression|reconcile|reconciliation|quarantine|backup|bak)([^[:alnum:]]|_|/|$)' \
        "$WORK/r${n}_files.txt" 2>/dev/null; then
        REWORK[$n]="YES"
    fi

    # --------------------------------------------------------
    # EXTRACT DEPENDENCY / SUPERSESSION SIGNALS
    # --------------------------------------------------------

    : > "$WORK/r${n}_signals.txt"

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        # Only textual files <= 2MB.
        size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
        [ "$size" -le 2000000 ] 2>/dev/null || continue

        grep -Ei \
            'SUPERSEDES|SUPERSEDED_BY|SUPERSEDED BY|PREVIOUS|NEXT_STAGE|NEXT STAGE|BASELINE|RECONCILES|DEPENDS_ON|DEPENDENCIES|REQUIRES|BLOCKER|OPEN_REVIEW|FINAL_AUTHORITY|FINAL AUTHORITY' \
            "$f" 2>/dev/null \
            | head -n 80 \
            | sed "s#^#$f: #" \
            >> "$WORK/r${n}_signals.txt" || true

    done < "$WORK/r${n}_files.txt"

    # --------------------------------------------------------
    # EXTRACT STATUS/RESULT FROM REPORTS
    # --------------------------------------------------------

    : > "$WORK/r${n}_status_lines.txt"

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
        [ "$size" -le 3000000 ] 2>/dev/null || continue

        grep -E \
            '(^|[^[:alnum:]_])(STATUS|RESULT|EXIT_CODE|EXIT STATUS|FINAL_STATUS|FINAL RESULT)[[:space:]]*=' \
            "$f" 2>/dev/null \
            | tail -n 40 \
            | sed "s#^#$f: #" \
            >> "$WORK/r${n}_status_lines.txt" || true

    done < "$WORK/r${n}_reports.txt"

    # --------------------------------------------------------
    # FIND LATEST REPORT BY MTIME
    # --------------------------------------------------------

    latest_file=""
    latest_epoch=0

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        e="$(file_epoch "$f")"

        if [ "$e" -ge "$latest_epoch" ] 2>/dev/null; then
            latest_epoch="$e"
            latest_file="$f"
        fi
    done < "$WORK/r${n}_reports.txt"

    if [ -n "$latest_file" ]; then

        LATEST_REPORT[$n]="$latest_file"

        # Find last explicit STATUS.
        status_line="$(grep -E \
            '(^|[^[:alnum:]_])(STATUS|FINAL_STATUS)[[:space:]]*=' \
            "$latest_file" 2>/dev/null | tail -n 1 || true)"

        result_line="$(grep -E \
            '(^|[^[:alnum:]_])(RESULT|FINAL_RESULT)[[:space:]]*=' \
            "$latest_file" 2>/dev/null | tail -n 1 || true)"

        exit_line="$(grep -E \
            '(^|[^[:alnum:]_])(EXIT_CODE|EXIT_STATUS)[[:space:]]*=' \
            "$latest_file" 2>/dev/null | tail -n 1 || true)"

        status="$(printf '%s\n' "$status_line" | sed -E 's/.*(STATUS|FINAL_STATUS)[[:space:]]*=[[:space:]]*//I' | tail -n 1)"
        result="$(printf '%s\n' "$result_line" | sed -E 's/.*(RESULT|FINAL_RESULT)[[:space:]]*=[[:space:]]*//I' | tail -n 1)"
        exitc="$(printf '%s\n' "$exit_line" | sed -E 's/.*(EXIT_CODE|EXIT_STATUS)[[:space:]]*=[[:space:]]*//I' | tail -n 1)"

        [ -n "$status" ] || status="UNKNOWN"
        [ -n "$result" ] || result="UNKNOWN"
        [ -n "$exitc" ] || exitc="UNKNOWN"

        LATEST_STATUS[$n]="$status"
        LATEST_RESULT[$n]="$result"
        LATEST_EXIT[$n]="$exitc"

        echo "LATEST_REPORT=$latest_file"
        echo "LATEST_REPORT_TIME=$(file_time "$latest_file")"
        echo "LATEST_STATUS=$status"
        echo "LATEST_RESULT=$result"
        echo "LATEST_EXIT_CODE=$exitc"

        LAST_EXEC[$n]="$(file_time "$latest_file")"
        LAST_EPOCH[$n]="$latest_epoch"

    fi

    # --------------------------------------------------------
    # FIRST EXECUTION / FIRST REPORT
    # --------------------------------------------------------

    first_file=""
    first_epoch=0

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        e="$(file_epoch "$f")"

        if [ "$first_epoch" -eq 0 ] || [ "$e" -lt "$first_epoch" ] 2>/dev/null; then
            first_epoch="$e"
            first_file="$f"
        fi
    done < "$WORK/r${n}_reports.txt"

    if [ -n "$first_file" ]; then
        FIRST_EXEC[$n]="$(file_time "$first_file")"
        FIRST_EPOCH[$n]="$first_epoch"
        echo "FIRST_EXECUTION_INFERRED_FROM=$(basename "$first_file")"
        echo "FIRST_EXECUTION=$(file_time "$first_file")"
    fi

    # --------------------------------------------------------
    # OPEN REVIEW DETECTION
    # --------------------------------------------------------

    all_text="$WORK/r${n}_all_text.txt"
    : > "$all_text"

    while IFS= read -r f; do
        [ -f "$f" ] || continue
        size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
        [ "$size" -le 2000000 ] 2>/dev/null || continue

        grep -Eis \
            'REVIEW_REQUIRED|REVIEW[[:space:]]*$|STATUS=REVIEW|STATUS=OPEN|STATUS=BLOCKED|OPEN_REVIEW|HUMAN_REVIEW|MANUAL_REVIEW|PRECONDITION_FAILED|RECONCILIATION_REQUIRED|INCOMPLETE|NOT_CLOSED|NOT_CLOSED|PENDING' \
            "$f" 2>/dev/null \
            | head -n 100 \
            >> "$all_text" || true

    done < "$WORK/r${n}_files.txt"

    if [ -s "$all_text" ]; then
        OPEN_REVIEW[$n]="YES"
    fi

    # --------------------------------------------------------
    # CONFLICT DETECTION
    # --------------------------------------------------------

    if [ -f "$WORK/r${n}_status_lines.txt" ]; then

        pass_count="$(grep -Eic \
            'STATUS[[:space:]]*=[[:space:]]*(PASS|PASSED|CLOSED|COMPLETE|COMPLETED|SUCCESS)|RESULT[[:space:]]*=.*(PASS|CLOSED|COMPLETE|SUCCESS)' \
            "$WORK/r${n}_status_lines.txt" 2>/dev/null || echo 0)"

        fail_count="$(grep -Eic \
            'STATUS[[:space:]]*=[[:space:]]*(FAIL|FAILED|ERROR|BLOCKED)|RESULT[[:space:]]*=.*(FAIL|FAILED|ERROR|BLOCKED)' \
            "$WORK/r${n}_status_lines.txt" 2>/dev/null || echo 0)"

        review_count="$(grep -Eic \
            'STATUS[[:space:]]*=[[:space:]]*(REVIEW|OPEN|PENDING)|RESULT[[:space:]]*=.*(REVIEW|OPEN|PENDING)' \
            "$WORK/r${n}_status_lines.txt" 2>/dev/null || echo 0)"

        if [ "$pass_count" -gt 0 ] && { [ "$fail_count" -gt 0 ] || [ "$review_count" -gt 0 ]; }; then
            CONFLICT[$n]="YES"
        fi

    fi

    # --------------------------------------------------------
    # SUPERSESSION EXTRACTION
    # --------------------------------------------------------

    if [ -s "$WORK/r${n}_signals.txt" ]; then

        supersedes="$(grep -Ei 'SUPERSEDES|SUPERSEDES:' "$WORK/r${n}_signals.txt" \
            | grep -Eo 'R[0-9]{1,2}' \
            | sort -u \
            | tr '\n' ',' \
            | sed 's/,$//' || true)"

        superseded_by="$(grep -Ei 'SUPERSEDED_BY|SUPERSEDED BY' "$WORK/r${n}_signals.txt" \
            | grep -Eo 'R[0-9]{1,2}' \
            | sort -u \
            | tr '\n' ',' \
            | sed 's/,$//' || true)"

        deps="$(grep -Ei 'DEPENDS_ON|DEPENDENCIES|REQUIRES|PREVIOUS|BASELINE|RECONCILES|NEXT_STAGE|NEXT STAGE' "$WORK/r${n}_signals.txt" \
            | grep -Eo 'R[0-9]{1,2}' \
            | sort -u \
            | tr '\n' ',' \
            | sed 's/,$//' || true)"

        [ -n "$supersedes" ] && SUPERSEDES[$n]="$supersedes"
        [ -n "$superseded_by" ] && SUPERSEDED_BY[$n]="$superseded_by"
        [ -n "$deps" ] && DEPENDENCIES[$n]="$deps"

    fi

    # --------------------------------------------------------
    # FINAL AUTHORITY
    # --------------------------------------------------------

    if [ -n "$latest_file" ]; then

        authority_signal="$(grep -Eis \
            'FINAL_AUTHORITY|FINAL AUTHORITY|FINAL CLOSURE|FINAL INTEGRITY|CLOSURE ATTESTATION|DEFINITIVE|AUTHORITATIVE|CANONICAL|CLOSED' \
            "$latest_file" 2>/dev/null \
            | tail -n 10 || true)"

        if [ -n "$authority_signal" ]; then
            FINAL_AUTHORITY[$n]="EVIDENCE_PRESENT"
        fi

    fi

    # --------------------------------------------------------
    # STATE CLASSIFICATION
    # --------------------------------------------------------

    status_upper="$(printf '%s' "${LATEST_STATUS[$n]}" | tr '[:lower:]' '[:upper:]')"
    result_upper="$(printf '%s' "${LATEST_RESULT[$n]}" | tr '[:lower:]' '[:upper:]')"
    exit_upper="$(printf '%s' "${LATEST_EXIT[$n]}" | tr '[:lower:]' '[:upper:]')"

    if [ "$FC" -eq 0 ]; then

        STATE[$n]="NOT_FOUND"

    elif [ "${OPEN_REVIEW[$n]}" = "YES" ]; then

        STATE[$n]="OPEN_REVIEW"

    elif printf '%s %s\n' "$status_upper" "$result_upper" \
        | grep -Eq 'FAIL|FAILED|ERROR|BLOCKED|PRECONDITION_FAILED'; then

        STATE[$n]="ERROR"

    elif [ "$exit_upper" != "UNKNOWN" ] && \
         printf '%s' "$exit_upper" | grep -Eq '^[1-9][0-9]*$'; then

        STATE[$n]="ERROR"

    elif printf '%s %s\n' "$status_upper" "$result_upper" \
        | grep -Eq 'PASS|PASSED|CLOSED|COMPLETE|COMPLETED|SUCCESS'; then

        if [ "${CONFLICT[$n]}" = "YES" ]; then
            STATE[$n]="OPEN_REVIEW"
        else
            STATE[$n]="DONE"
        fi

    else

        STATE[$n]="INCOMPLETE"

    fi

    # --------------------------------------------------------
    # LIVE SUMMARY FOR THIS R
    # --------------------------------------------------------

    echo "REWORK=${REWORK[$n]}"
    echo "CONFLICT=${CONFLICT[$n]}"
    echo "OPEN_REVIEW=${OPEN_REVIEW[$n]}"
    echo "FINAL_AUTHORITY=${FINAL_AUTHORITY[$n]}"
    echo "SUPERSEDES=${SUPERSEDES[$n]}"
    echo "SUPERSEDED_BY=${SUPERSEDED_BY[$n]}"
    echo "DEPENDENCIES=${DEPENDENCIES[$n]}"
    echo "STATE=${STATE[$n]}"

done

# ------------------------------------------------------------
# CROSS-R DEPENDENCY / SUPERSESSION RECONCILIATION
# ------------------------------------------------------------

section "5. CROSS-R SUPERSESSION / DEPENDENCY RECONCILIATION"

for n in $(seq 1 65); do

    [ "${FILE_COUNT[$n]}" -gt 0 ] || continue

    printf 'R%-2s  state=%-12s supersedes=%-18s superseded_by=%-18s deps=%s\n' \
        "$n" \
        "${STATE[$n]}" \
        "${SUPERSEDES[$n]}" \
        "${SUPERSEDED_BY[$n]}" \
        "${DEPENDENCIES[$n]}"

done

# ------------------------------------------------------------
# P0 BRANCH SUMMARY
# ------------------------------------------------------------

section "6. P0 BRANCH SUMMARY"

for p in P0-01 p0_01 p0_02 p0_03; do
    count="$(grep -Eic "/${p}/|_${p}_|${p}" "$WORK/all_files.txt" 2>/dev/null || echo 0)"
    printf '%-10s %s files\n' "$p" "$count"
done

# ------------------------------------------------------------
# CURRENT TIMELINE / STALENESS CHECK
# ------------------------------------------------------------

section "7. DECISION MAP / META AUDIT / CURRENT STATE TIMELINE"

for f in \
    "$PROJECT"/P0_R1_R65_DECISION_MAP_*.txt \
    "$PROJECT"/P0_R1_R65_META_AUDIT_*.txt \
    "$PROJECT"/P0_R1_R65_CLOSURE_TRUTH_MAP_*.txt
do
    [ -f "$f" ] || continue
    printf '%-70s %s\n' \
        "$(basename "$f")" \
        "$(file_time "$f")"
done

echo
echo "Files created AFTER the latest decision map:"
latest_decision="$(
    ls -1t "$PROJECT"/P0_R1_R65_DECISION_MAP_*.txt 2>/dev/null \
    | head -n 1 || true
)"

if [ -n "$latest_decision" ]; then

    decision_epoch="$(file_epoch "$latest_decision")"

    while IFS= read -r f; do
        [ -f "$f" ] || continue

        e="$(file_epoch "$f")"

        if [ "$e" -gt "$decision_epoch" ] 2>/dev/null; then
            printf '%s | %s\n' \
                "$(file_time "$f")" \
                "$f"
        fi

    done < "$WORK/all_files.txt" \
        | sort \
        | tail -n 100

else
    echo "No decision map found."
fi

# ------------------------------------------------------------
# R62+ CURRENT CONFIG SHAPE ONLY
# ------------------------------------------------------------

section "8. CURRENT REGISTRY AUTHORITY SHAPE"

for f in \
    "$PROJECT"/docker-compose.yml \
    "$PROJECT"/compose.yml \
    "$PROJECT"/deploy.sh \
    "$PROJECT"/deploy/*.sh \
    "$PROJECT"/.github/workflows/*.yml \
    "$PROJECT"/.github/workflows/*.yaml
do

    [ -f "$f" ] || continue

    echo
    echo "FILE=$f"

    grep -En \
        'RELEASE_ID|IMAGE_TAG|REGISTRY_IMAGE_PREFIX|image:|docker build|docker push|docker tag' \
        "$f" 2>/dev/null \
        | sed -E \
            's/(RELEASE_ID|IMAGE_TAG|REGISTRY_IMAGE_PREFIX)=([^[:space:]]+)/\1=<VALUE_REDACTED>/g' \
        | head -n 120

done

# ------------------------------------------------------------
# GIT STATE
# ------------------------------------------------------------

section "9. GIT STATE"

git status --short 2>/dev/null || true

echo
echo "RECENT_COMMITS"
git log -12 --date=iso --pretty=format:'%h | %ad | %s' 2>/dev/null || true

# ------------------------------------------------------------
# FINAL TABLE
# ------------------------------------------------------------

section "10. FINAL CLOSURE TRUTH TABLE R1-R65"

echo
echo "STATE LEGEND:"
echo "  DONE         = latest evidence indicates successful/closed completion"
echo "  INCOMPLETE   = artifact exists, but no authoritative terminal closure was found"
echo "  ERROR        = latest evidence indicates failure/error/non-zero execution"
echo "  OPEN_REVIEW  = review/open/blocker/reconciliation evidence remains"
echo "  NOT_FOUND    = no R-specific evidence discovered"
echo
echo "IMPORTANT:"
echo "  DONE does NOT mean 'a script exists'."
echo "  DONE requires terminal success/closure evidence."
echo "  OPEN_REVIEW takes precedence over older PASS evidence."
echo "  Conflicting historical PASS/FAIL/REVIEW evidence is conservatively OPEN_REVIEW."
echo

printf '%-4s | %-19s | %-19s | %-38s | %-18s | %-42s | %-7s | %-9s | %-12s\n' \
    "R" \
    "FIRST_EXECUTION" \
    "LAST_EXECUTION" \
    "LATEST_REPORT" \
    "LATEST_STATUS" \
    "LATEST_RESULT" \
    "EXIT" \
    "OPEN_REVIEW" \
    "FINAL_AUTH"

printf '%s\n' \
'----+---------------------+---------------------+----------------------------------------+--------------------+--------------------------------------------+---------+-----------+-------------'

for n in $(seq 1 65); do

    report_display="${LATEST_REPORT[$n]}"

    if [ "$report_display" = "NOT_FOUND" ]; then
        report_display="NOT_FOUND"
    else
        report_display="$(basename "$report_display")"
    fi

    printf '%-4s | %-19s | %-19s | %-38s | %-18s | %-42s | %-7s | %-9s | %-12s\n' \
        "R$n" \
        "${FIRST_EXEC[$n]}" \
        "${LAST_EXEC[$n]}" \
        "$report_display" \
        "${LATEST_STATUS[$n]}" \
        "${LATEST_RESULT[$n]}" \
        "${LATEST_EXIT[$n]}" \
        "${OPEN_REVIEW[$n]}" \
        "${FINAL_AUTHORITY[$n]}"

done

echo
echo "============================================================"
echo "SECONDARY STATE TABLE"
echo "============================================================"

printf '%-4s | %-12s | %-7s | %-9s | %-18s | %-18s | %-18s | %-7s\n' \
    "R" \
    "STATE" \
    "FILES" \
    "REPORTS" \
    "SUPERSEDES" \
    "SUPERSEDED_BY" \
    "DEPENDENCIES" \
    "REWORK"

printf '%s\n' \
'----+--------------+---------+----------+--------------------+--------------------+--------------------+--------'

for n in $(seq 1 65); do

    printf '%-4s | %-12s | %-7s | %-9s | %-18s | %-18s | %-18s | %-7s\n' \
        "R$n" \
        "${STATE[$n]}" \
        "${FILE_COUNT[$n]}" \
        "${REPORT_COUNT[$n]}" \
        "${SUPERSEDES[$n]}" \
        "${SUPERSEDED_BY[$n]}" \
        "${DEPENDENCIES[$n]}" \
        "${REWORK[$n]}"

done

# ------------------------------------------------------------
# MACHINE SUMMARY
# ------------------------------------------------------------

section "11. MACHINE SUMMARY"

DONE_COUNT=0
INCOMPLETE_COUNT=0
ERROR_COUNT=0
OPEN_COUNT=0
NOTFOUND_COUNT=0

for n in $(seq 1 65); do
    case "${STATE[$n]}" in
        DONE) DONE_COUNT=$((DONE_COUNT+1)) ;;
        INCOMPLETE) INCOMPLETE_COUNT=$((INCOMPLETE_COUNT+1)) ;;
        ERROR) ERROR_COUNT=$((ERROR_COUNT+1)) ;;
        OPEN_REVIEW) OPEN_COUNT=$((OPEN_COUNT+1)) ;;
        NOT_FOUND) NOTFOUND_COUNT=$((NOTFOUND_COUNT+1)) ;;
    esac
done

echo "TOTAL_R_GATES=65"
echo "DONE=$DONE_COUNT"
echo "INCOMPLETE=$INCOMPLETE_COUNT"
echo "ERROR=$ERROR_COUNT"
echo "OPEN_REVIEW=$OPEN_COUNT"
echo "NOT_FOUND=$NOTFOUND_COUNT"

echo
echo "DONE_R_LIST"
for n in $(seq 1 65); do
    [ "${STATE[$n]}" = "DONE" ] && printf 'R%s ' "$n"
done
echo

echo "INCOMPLETE_R_LIST"
for n in $(seq 1 65); do
    [ "${STATE[$n]}" = "INCOMPLETE" ] && printf 'R%s ' "$n"
done
echo

echo "ERROR_R_LIST"
for n in $(seq 1 65); do
    [ "${STATE[$n]}" = "ERROR" ] && printf 'R%s ' "$n"
done
echo

echo "OPEN_REVIEW_R_LIST"
for n in $(seq 1 65); do
    [ "${STATE[$n]}" = "OPEN_REVIEW" ] && printf 'R%s ' "$n"
done
echo

echo "NOT_FOUND_R_LIST"
for n in $(seq 1 65); do
    [ "${STATE[$n]}" = "NOT_FOUND" ] && printf 'R%s ' "$n"
done
echo

# ------------------------------------------------------------
# STRONG WARNINGS
# ------------------------------------------------------------

section "12. CLOSURE WARNINGS"

if [ "$OPEN_COUNT" -gt 0 ]; then
    echo "WARNING: OPEN_REVIEW gates exist."
fi

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "WARNING: ERROR gates exist."
fi

if [ "$INCOMPLETE_COUNT" -gt 0 ]; then
    echo "WARNING: INCOMPLETE gates exist."
fi

if [ "$NOTFOUND_COUNT" -gt 0 ]; then
    echo "WARNING: NOT_FOUND gates exist."
fi

if [ "$DONE_COUNT" -eq 65 ]; then
    echo
    echo "CAUTION: All R gates classify as DONE, but this is NOT by itself proof"
    echo "that the entire P0→R1-R65 chain is production-ready."
    echo "Cross-gate authority and dependency reconciliation still matter."
fi

echo
echo "============================================================"
echo "CLOSURE TRUTH MAP COMPLETE"
echo "============================================================"
echo "OUTPUT=$OUT"
echo "WORKDIR=$WORK"
echo "============================================================"
echo

# ------------------------------------------------------------
# SMALL FINAL TERMINAL POINTER
# ------------------------------------------------------------

echo "FINAL TABLE IS ABOVE."
echo
echo "To inspect only the final state table later:"
echo "sed -n '/FINAL CLOSURE TRUTH TABLE R1-R65/,/SECONDARY STATE TABLE/p' \"$OUT\""
echo
echo "To inspect only the machine summary later:"
echo "sed -n '/MACHINE SUMMARY/,/CLOSURE WARNINGS/p' \"$OUT\""

exit 0
