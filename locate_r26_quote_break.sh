#!/usr/bin/env bash
set -u

FILE="phase_p0_02_r26_secret_provenance_ground_truth_parser.sh"

echo "============================================================"
echo "R26 QUOTE-BREAK LOCATOR"
echo "============================================================"

if [ ! -f "$FILE" ]; then
    echo "FAIL: FILE_NOT_FOUND=$FILE"
    exit 20
fi

echo
echo "1. BASH SYNTAX"
echo "============================================================"

bash -n "$FILE" 2>&1
RC=$?

echo "BASH_N_RC=$RC"

echo
echo "2. QUOTE STATE PER LINE"
echo "============================================================"

awk '
BEGIN {
    dq=0
    sq=0
    esc=0
}
{
    line=$0
    for (i=1; i<=length(line); i++) {
        c=substr(line,i,1)

        if (esc) {
            esc=0
            continue
        }

        if (c=="\\") {
            esc=1
            continue
        }

        if (c=="\"" && sq==0) {
            dq = 1-dq
        }
        else if (c=="'\''" && dq==0) {
            sq = 1-sq
        }
    }

    printf "%4d  DQ=%d SQ=%d  %s\n", NR, dq, sq, line
}
END {
    print ""
    print "FINAL_DQ=" dq
    print "FINAL_SQ=" sq
}
' "$FILE" | tail -n 120

echo
echo "3. SUSPECTED OPEN DOUBLE-QUOTE"
echo "============================================================"

awk '
BEGIN {
    dq=0
    sq=0
    esc=0
}
{
    line=$0
    before=dq

    for (i=1; i<=length(line); i++) {
        c=substr(line,i,1)

        if (esc) {
            esc=0
            continue
        }

        if (c=="\\") {
            esc=1
            continue
        }

        if (c=="\"" && sq==0) {
            dq=1-dq
        }
        else if (c=="'\''" && dq==0) {
            sq=1-sq
        }
    }

    if (dq != before) {
        printf "QUOTE_STATE_CHANGE LINE=%d BEFORE_DQ=%d AFTER_DQ=%d\n", NR, before, dq
        print "TEXT=" line
        print ""
    }
}
' "$FILE"

echo
echo "4. LAST 160 LINES"
echo "============================================================"

nl -ba "$FILE" | tail -n 160

echo
echo "5. READ-ONLY GUARANTEES"
echo "============================================================"

echo "READ_ONLY=YES"
echo "NO_SOURCE_WRITES=YES"
echo "NO_RUNTIME_EXECUTION=YES"
echo "NO_BUILD=YES"
echo "NO_DEPLOYMENT=YES"
echo "NO_DELETIONS=YES"

echo
echo "============================================================"
echo "R26 QUOTE-BREAK LOCATOR COMPLETE"
echo "============================================================"
