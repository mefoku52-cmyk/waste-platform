#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_master_map_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "MASTER AUDIT MAP"
echo "P0 + R1-R76"
echo "TIME=$(date -Is)"
echo "============================================================"

TMP=$(mktemp)

find . \
  -type f \
  \( -name '*.txt' -o -name '*.log' -o -name '*.md' \) \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './vendor/*' \
  -not -path './dist/*' \
  -not -path './build/*' \
  -not -path './target/*' \
  -not -name '*_all_text*' \
  -not -name '*all_text*' \
  -not -name '*closure_truth*' \
  -not -name '*frontier*' \
  -print 2>/dev/null |
while IFS= read -r f; do

    base=$(basename "$f")

    # P0 audit
    if printf '%s\n' "$base" | grep -qiE '^p0([_-]|\.|$)'; then
        id="P0"
    else
        # R audit ID z názvu súboru
        id=$(printf '%s\n' "$base" |
          grep -oEi '(^|[^a-z])r[0-9]+(_|-|\.|$)' |
          head -1 |
          grep -oEi 'r[0-9]+' |
          tr '[:lower:]' '[:upper:]' || true)
    fi

    [ -n "$id" ] || continue

    result=$(grep -hEi \
      '^(RESULT|VERDICT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
      "$f" 2>/dev/null | tail -1 || true)

    [ -n "$result" ] || continue

    printf '%s\t%s\t%s\n' "$id" "$base" "$result"

done > "$TMP"

echo
echo "=== P0 AUDITS ==="

awk -F '\t' '$1=="P0" {
    printf "%-5s | %-75s | %s\n", $1, $2, $3
}' "$TMP"

echo
echo "=== R AUDITS ==="

sort -t $'\t' -k1,1V "$TMP" |
awk -F '\t' '$1 ~ /^R[0-9]+$/ {
    printf "%-5s | %-75s | %s\n", $1, $2, $3
}'

echo
echo "=== R COUNT ==="

RCOUNT=$(awk -F '\t' '$1 ~ /^R[0-9]+$/ {print $1}' "$TMP" |
         sort -Vu | wc -l)

echo "R_AUDITS_FOUND=$RCOUNT"

echo
echo "=== RESULT COUNTS ==="

awk -F '\t' '
{
    x=$3
    sub(/^[A-Z_]+=/,"",x)

    if (x ~ /PASS|CLEAN|CLOSED|CONFIRMED|VALID|IMPLEMENTED/)
        pass++
    else if (x ~ /FAIL|FAILURE/)
        fail++
    else if (x ~ /BLOCKED/)
        blocked++
    else if (x ~ /REVIEW|REQUIRES|PENDING/)
        review++
}
END {
    printf "PASS/CLEAN/CLOSED/CONFIRMED/VALID/IMPLEMENTED=%d\n",pass+0
    printf "FAIL/FAILURE=%d\n",fail+0
    printf "BLOCKED=%d\n",blocked+0
    printf "REVIEW/REQUIRES/PENDING=%d\n",review+0
}' "$TMP"

echo
echo "=== CURRENT DEPLOYMENT ==="

for f in r75_deployment_identity_*.txt \
         r76_deployment_active_gate_*.txt \
         r77_deployment_trigger_gate_*.txt
do
    [ -f "$f" ] || continue

    echo "--- $(basename "$f") ---"

    grep -Ei \
      '^(VERDICT|RESULT|STATUS|WORKFLOW_COUNT|DEPLOY_TRIGGER_REFERENCES|SAFETY|SECRETS)=' \
      "$f" 2>/dev/null || true
done

rm -f "$TMP"

echo
echo "============================================================"
echo "END"
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"
echo "============================================================"

} | tee "$OUT"
