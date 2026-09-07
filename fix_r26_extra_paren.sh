#!/data/data/com.termux/files/usr/bin/bash

set -u

FILE="phase_p0_02_r26_secret_provenance_ground_truth_parser.sh"

echo "============================================================"
echo "R26 MINIMAL EXTRA-PAREN FIX"
echo "============================================================"

if [ ! -f "$FILE" ]; then
    echo "FAIL: FILE_NOT_FOUND=$FILE"
    exit 20
fi

echo
echo "1. CURRENT BLOCK"
echo "============================================================"

nl -ba "$FILE" | sed -n '429,441p'

echo
echo "2. APPLY EXACT ONE-LINE FIX"
echo "============================================================"

python3 - <<'PY'
from pathlib import Path

p = Path("phase_p0_02_r26_secret_provenance_ground_truth_parser.sh")
s = p.read_text()

old = '''    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\\n' "$OUTPUT_HITS" | grep -c . || true
    )"
    )
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
'''

new = '''    SECRET_VALUE_OUTPUT_COUNT="$(
        printf '%s\\n' "$OUTPUT_HITS" | grep -c . || true
    )"
    fail "POTENTIAL_SECRET_VALUE_OUTPUT_DETECTED COUNT=$SECRET_VALUE_OUTPUT_COUNT"
'''

if old not in s:
    raise SystemExit("FAIL: EXACT_EXTRA_PAREN_BLOCK_NOT_FOUND")

s = s.replace(old, new, 1)

p.write_text(s)

print("PASS: EXTRA_PAREN_REMOVED")
PY

echo
echo "3. FIXED BLOCK"
echo "============================================================"

nl -ba "$FILE" | sed -n '429,441p'

echo
echo "4. BASH SYNTAX"
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
echo "5. READ-ONLY GUARANTEES"
echo "============================================================"

echo "SOURCE_WRITE_SCOPE=ONE_SCRIPT_ONLY"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"
echo "NO_SECRET_VALUES_PRINTED=YES"

echo
echo "============================================================"
echo "R26 MINIMAL EXTRA-PAREN FIX COMPLETE"
echo "============================================================"
