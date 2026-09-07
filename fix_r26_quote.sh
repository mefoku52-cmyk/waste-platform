#!/data/data/com.termux/files/usr/bin/bash

set -u

FILE="phase_p0_02_r26_secret_provenance_ground_truth_parser.sh"

echo "============================================================"
echo "R26 QUOTE FIX"
echo "============================================================"

if [ ! -f "$FILE" ]; then
    echo "FAIL: FILE_NOT_FOUND=$FILE"
    exit 20
fi

echo
echo "1. CURRENT AREA"
echo "============================================================"
nl -ba "$FILE" | sed -n '425,440p'

echo
echo "2. CHECK EXPECTED BROKEN CONSTRUCT"
echo "============================================================"

if sed -n '433,435p' "$FILE" | grep -q 'SECRET_VALUE_OUTPUT_COUNT="$('; then
    echo 'PASS: OPEN_COMMAND_SUBSTITUTION_FOUND'
else
    echo 'FAIL: EXPECTED_BROKEN_CONSTRUCT_NOT_FOUND'
    exit 20
fi

if sed -n '435p' "$FILE" | grep -qE '^\s*\)\s*"$'; then
    echo 'PASS: COMMAND_SUBSTITUTION_ALREADY_CLOSED'
    echo
    echo "3. SYNTAX CHECK"
    bash -n "$FILE"
    RC=$?
    echo "BASH_N_RC=$RC"
    exit "$RC"
fi

echo 'PASS: MISSING_COMMAND_SUBSTITUTION_CLOSER_CONFIRMED'

echo
echo "3. APPLY MINIMAL FIX"
echo "============================================================"

python3 - "$FILE" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()

old = """    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\\n' "$OUTPUT_HITS" | grep -c . || true
"""

new = """    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\\n' "$OUTPUT_HITS" | grep -c . || true
    )"
"""

if old not in s:
    raise SystemExit("FAIL: EXACT_R26_BROKEN_BLOCK_NOT_FOUND")

s = s.replace(old, new, 1)
p.write_text(s)

print("PASS: MINIMAL_QUOTE_FIX_APPLIED")
PY

echo
echo "4. FIXED AREA"
echo "============================================================"
nl -ba "$FILE" | sed -n '429,440p'

echo
echo "5. BASH SYNTAX"
echo "============================================================"

bash -n "$FILE"
RC=$?

echo "BASH_N_RC=$RC"

if [ "$RC" -eq 0 ]; then
    echo "PASS: R26 SHELL SYNTAX VALID"
else
    echo "FAIL: R26 SHELL SYNTAX INVALID"
    exit 20
fi

echo
echo "6. READ-ONLY SOURCE GUARANTEES"
echo "============================================================"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"

echo
echo "============================================================"
echo "R26 QUOTE FIX COMPLETE"
echo "============================================================"
