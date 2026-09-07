#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="${1:-$PWD}"
TS="$(date '+%Y%m%d_%H%M%S')"
OUT="$ROOT/R_REQUIREMENT_COMPLIANCE_$TS.txt"

cd "$ROOT" || exit 1

{
echo "============================================================"
echo "R REQUIREMENT COMPLIANCE AUDIT"
echo "PROJECT=$ROOT"
echo "TIME=$(date -Is)"
echo "MODE=READ_ONLY"
echo "============================================================"
echo

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

result_from_file() {
    local f="$1"
    grep -E '^[[:space:]]*(RESULT|VERDICT)=' "$f" 2>/dev/null \
        | tail -1 \
        | sed 's/^[[:space:]]*//'
}

purpose_from_result() {
    local r="$1"

    case "$r" in
        R1|R2|R3|R4|R5|R6|R7|R8)
            echo "P0-01/P0-02 boundary or secret-wiring control"
            ;;
        R9|R10)
            echo "Runtime secret authority and cross-authority closure"
            ;;
        R11|R12|R13|R14|R15|R16|R17|R18|R19|R20|R21|R22|R23|R24|R25|R26|R27|R28|R29|R30|R31|R32|R33|R34|R35|R36)
            echo "Secret provenance, parser, lineage, reconciliation and closure"
            ;;
        R37|R38|R39|R40|R41)
            echo "Production-readiness chain and deterministic ledger closure"
            ;;
        R42|R43|R44|R45|R46|R47|R48)
            echo "Real production path, host/dataflow, reload and authority closure"
            ;;
        R49|R50|R51)
            echo "CI/CD deployment authority, architecture and deployment safety"
            ;;
        R52|R53)
            echo "Rollback and recovery authority"
            ;;
        R54|R55|R56)
            echo "Release identity authority and CI deployment handoff"
            ;;
        R57|R58|R59|R60|R61|R62|R63|R64|R65|R66|R67|R68|R69|R70|R71|R72|R73|R74)
            echo "Post-release/deployment closure stage"
            ;;
        R75)
            echo "Deployment identity provenance"
            ;;
        R76)
            echo "Active deployment workflow/authority"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

requirement_from_result() {
    local r="$1"

    case "$r" in
        R1) echo "Secret assignment boundary must be demonstrably correct." ;;
        R2) echo "Secret values/tokens must be handled without false semantic classification." ;;
        R3) echo "Secret authority boundary must be closed." ;;
        R4) echo "Secret wiring boundary must be correct." ;;
        R5) echo "Secret wiring semantic interpretation must be resolved." ;;
        R6) echo "Secret wiring context must be correct." ;;
        R7) echo "Compose secret token proof must succeed." ;;
        R8) echo "Compose secret context must be correctly classified." ;;
        R9) echo "Runtime secret authority must be closed." ;;
        R10) echo "Cross-authority secret closure must hold." ;;
        R11) echo "Secret provenance lineage must be closed." ;;
        R12) echo "Provenance analyzer must be sufficiently hardened." ;;
        R13) echo "Compose secret provenance semantics must be correct." ;;
        R14) echo "Analyzer consistency must hold." ;;
        R15) echo "Expected provenance counts must close." ;;
        R16) echo "Final secret provenance lineage must close." ;;
        R17) echo "Known false positives must be closed." ;;
        R18) echo "Provenance stability gate must pass." ;;
        R19) echo "Parser reconciliation must be deterministic." ;;
        R20) echo "Semantic provenance reconciliation must close." ;;
        R21) echo "Deterministic parser closure must pass." ;;
        R22) echo "Semantic parser final closure must pass." ;;
        R23) echo "Ground-truth provenance stage must have a verifiable result." ;;
        R24) echo "Ground-truth provenance closure must pass." ;;
        R25) echo "Ground-truth deterministic analysis must pass." ;;
        R26) echo "Baseline/ground-truth parser state must be resolved without conflict." ;;
        R27) echo "Post-R26 integrity must be demonstrated." ;;
        R28) echo "Post-R27 regression must be resolved." ;;
        R29) echo "Cross-file provenance consistency must be demonstrated." ;;
        R30) echo "Provenance regression closure must be demonstrated." ;;
        R31) echo "R26-R30 forensic reconciliation must close." ;;
        R32) echo "Secret-output false positives must be correctly located/classified." ;;
        R33) echo "Final secret provenance classification must pass." ;;
        R34) echo "Corrected provenance scope must pass." ;;
        R35) echo "Final provenance integrity must pass." ;;
        R36) echo "Closure attestation must be supported." ;;
        R37) echo "Production-readiness chain must be discoverable." ;;
        R38) echo "Production-readiness ledger must normalize successfully." ;;
        R39) echo "Superseded evidence must be reconciled." ;;
        R40) echo "Production-readiness ledger must be deterministic." ;;
        R41) echo "Production-readiness ledger must reach closure." ;;
        R42) echo "Real production readiness must be demonstrated." ;;
        R43) echo "Production gaps must be classified and resolved." ;;
        R44) echo "Unsafe bind blocker must be resolved." ;;
        R45) echo "Application-to-host dataflow must be proven." ;;
        R46) echo "Application-to-host runtime dataflow must close." ;;
        R47) echo "Production reload dataflow must be proven without an unresolved blocker." ;;
        R48) echo "Production reload authority must be closed." ;;
        R49) echo "CI production deployment authority must be demonstrated." ;;
        R50) echo "CI deployment architecture must be correctly separated." ;;
        R51) echo "Production deployment safety authority must be closed." ;;
        R52) echo "Rollback/recovery authority must be demonstrated." ;;
        R53) echo "Recovery must exist and artifact rollback must have versioned release authority." ;;
        R54) echo "Release identity authority must be implemented." ;;
        R55) echo "Release identity transition after R54 must be independently verified." ;;
        R56) echo "Release identity contract must be valid and CI deploy handoff must be complete." ;;
        R57|R58|R59|R60|R61|R62|R63|R64|R65|R66|R67|R68|R69|R70|R71|R72|R73|R74)
            echo "Corresponding release/deployment closure requirement must be independently evidenced." ;;
        R75) echo "Deployment identity must be established from actual deployment authority." ;;
        R76) echo "An active deployment workflow/authority must exist and be discoverable." ;;
        *) echo "Requirement unknown." ;;
    esac
}

classify() {
    local result="$1"
    local evidence="$2"

    if [[ -z "$result" ]]; then
        echo "NOT_PROVEN"
        return
    fi

    if echo "$result" | grep -Eq 'FAIL|FAILURE|BLOCKED|REQUIRES_IMPLEMENTATION|PENDING|REVIEW_REQUIRED|REVIEW$|REVIEW_' ; then
        echo "NO"
        return
    fi

    if echo "$result" | grep -Eq 'PASS|CLEAN|CLOSED|CONFIRMED|VALID|IMPLEMENTED'; then
        echo "YES"
        return
    fi

    if [[ -n "$evidence" ]]; then
        echo "PARTIAL"
    else
        echo "NOT_PROVEN"
    fi
}

# ------------------------------------------------------------
# Candidate result files
# ------------------------------------------------------------

mapfile -t FILES < <(
    find . -type f -name '*.txt' \
        ! -path './.git/*' \
        ! -path './node_modules/*' \
        ! -path './vendor/*' \
        ! -path './dist/*' \
        ! -path './build/*' \
        ! -name 'GLOBAL_*' \
        ! -name 'P0_R*_R*_GLOBAL_*' \
        ! -name '*CLOSURE*' \
        ! -name '*DECISION_MAP*' \
        ! -name '*TRUTH_MAP*' \
        ! -name '*META_AUDIT*' \
        ! -name '*FRONTIER*' \
        ! -name 'r*_files.txt' \
        ! -name 'r*_reports.txt' \
        ! -name 'r*_signals.txt' \
        ! -name 'r*_status_lines.txt' \
        | sort
)

declare -A FOUND
declare -A RESULT
declare -A FILE

for f in "${FILES[@]}"; do
    base="$(basename "$f")"

    # Only exact R identity at filename beginning.
    rid="$(echo "$base" | sed -nE \
        's/^p0[-_]([0-9]+)[-_]r([0-9]+)[-_].*/R\2/p;
         s/^r([0-9]+)[-_].*/R\1/p')"

    [[ -z "$rid" ]] && continue

    res="$(result_from_file "$f")"
    [[ -z "$res" ]] && continue

    FOUND["$rid"]=1
    RESULT["$rid"]="${RESULT[$rid]:-}${RESULT[$rid]:+$'\n'}$res"
    FILE["$rid"]="${FILE[$rid]:-}${FILE[$rid]:+$'\n'}$f"
done

# ------------------------------------------------------------
# Evaluate R1-R76
# ------------------------------------------------------------

YES=0
NO=0
PARTIAL=0
NOT_PROVEN=0
MISSING=0
CONFLICT=0

echo "=== REQUIREMENT COMPLIANCE MAP ==="
echo

for n in $(seq 1 76); do
    r="R$n"

    purpose="$(purpose_from_result "$r")"
    req="$(requirement_from_result "$r")"

    results="${RESULT[$r]:-}"
    files="${FILE[$r]:-}"

    if [[ -z "$results" ]]; then
        status="NOT_PROVEN"
        MISSING=$((MISSING+1))
        conflict="NO"
        evidence="NO_RESULT_ARTIFACT"
    else
        # Detect contradictory result classes.
        if echo "$results" | grep -Eq 'PASS|CLEAN|CLOSED|CONFIRMED|VALID|IMPLEMENTED' &&
           echo "$results" | grep -Eq 'FAIL|FAILURE|BLOCKED|PENDING|REVIEW_REQUIRED|REQUIRES_IMPLEMENTATION'; then
            status="CONFLICT"
            CONFLICT=$((CONFLICT+1))
            conflict="YES"
        else
            status="$(classify "$results" "$files")"
            case "$status" in
                YES) YES=$((YES+1)) ;;
                NO) NO=$((NO+1)) ;;
                PARTIAL) PARTIAL=$((PARTIAL+1)) ;;
                NOT_PROVEN) NOT_PROVEN=$((NOT_PROVEN+1)) ;;
            esac
            conflict="NO"
        fi
        evidence="RESULT_ARTIFACT_FOUND"
    fi

    echo "------------------------------------------------------------"
    echo "$r"
    echo "PURPOSE=$purpose"
    echo "REQUIREMENT=$req"
    echo "EVIDENCE=$evidence"
    echo "COMPLIANCE=$status"
    echo "CONFLICT=$conflict"

    if [[ -n "$files" ]]; then
        echo "FILES:"
        printf '%s\n' "$files"
    fi

    if [[ -n "$results" ]]; then
        echo "RESULT:"
        printf '%s\n' "$results"
    fi

    echo
done

# ------------------------------------------------------------
# Deployment-specific hard gates
# ------------------------------------------------------------

echo "============================================================"
echo "DEPLOYMENT HARD-GATE CHECK"
echo "============================================================"

R75_FILE="$(find . -maxdepth 1 -type f -name 'r75_deployment_identity_*.txt' | sort | tail -1)"
R76_FILE="$(find . -maxdepth 1 -type f -name 'r76_deployment_active_gate_*.txt' | sort | tail -1)"

if [[ -n "$R75_FILE" ]]; then
    R75_VERDICT="$(grep -E '^(VERDICT|RESULT)=' "$R75_FILE" | tail -1)"
    echo "R75_FILE=$R75_FILE"
    echo "$R75_VERDICT"
else
    echo "R75_FILE=MISSING"
fi

if [[ -n "$R76_FILE" ]]; then
    R76_VERDICT="$(grep -E '^(VERDICT|RESULT)=' "$R76_FILE" | tail -1)"
    WORKFLOW="$(grep -E '^WORKFLOW_COUNT=' "$R76_FILE" | tail -1)"
    echo "R76_FILE=$R76_FILE"
    echo "$R76_VERDICT"
    echo "$WORKFLOW"
else
    echo "R76_FILE=MISSING"
fi

echo
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo "YES=$YES"
echo "NO=$NO"
echo "PARTIAL=$PARTIAL"
echo "NOT_PROVEN=$NOT_PROVEN"
echo "MISSING=$MISSING"
echo "CONFLICT=$CONFLICT"
echo

echo "============================================================"
echo "FINAL DECISION RULE"
echo "============================================================"
echo "PASS requires:"
echo "  - no missing mandatory R evidence"
echo "  - no unresolved conflict"
echo "  - no FAILED/BLOCKED/PENDING hard gate"
echo "  - deployment authority must be independently proven"
echo "  - active workflow must be proven where required"
echo

if [[ "$CONFLICT" -gt 0 ]]; then
    FINAL="FAIL_CONFLICTING_EVIDENCE"
elif [[ "$NO" -gt 0 ]]; then
    FINAL="FAIL_REQUIREMENT_NOT_SATISFIED"
elif [[ "$MISSING" -gt 0 ]]; then
    FINAL="NOT_PROVEN_MISSING_EVIDENCE"
elif [[ "$PARTIAL" -gt 0 || "$NOT_PROVEN" -gt 0 ]]; then
    FINAL="PARTIAL_NOT_FULLY_PROVEN"
else
    FINAL="PASS_ALL_REQUIREMENTS_PROVEN"
fi

echo "FINAL_VERDICT=$FINAL"
echo
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"
echo "============================================================"

} | tee "$OUT"
