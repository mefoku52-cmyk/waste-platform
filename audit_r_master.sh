#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_r_master_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "R MASTER RESULT MAP"
echo "R1-R76"
echo "TIME=$(date -Is)"
echo "============================================================"

echo
echo "=== R AUDITS DISCOVERED ==="

for n in $(seq 1 76); do

    files=$(find . -maxdepth 2 -type f \
      \( -iname "*_r${n}_*.txt" -o \
         -iname "*_r${n}_*.log" -o \
         -iname "*_r${n}_*.sh" -o \
         -iname "r${n}_*.txt" -o \
         -iname "r${n}_*.log" \) \
      -not -path './.git/*' \
      -not -path './node_modules/*' \
      -not -path './vendor/*' \
      -not -path './build/*' \
      -not -path './dist/*' \
      -not -name '*_all_text*' \
      2>/dev/null)

    [ -n "$files" ] || continue

    echo
    echo "--- R${n} ---"

    printf '%s\n' "$files" |
    while IFS= read -r f; do
        base=$(basename "$f")

        result=$(grep -hEi \
          '^(RESULT|VERDICT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
          "$f" 2>/dev/null | tail -1 || true)

        if [ -n "$result" ]; then
            echo "$base -> $result"
        else
            echo "$base -> NO_RESULT_LINE"
        fi
    done
done

echo
echo "=== DIRECT R75/R76 STATUS ==="

for f in r75_deployment_identity_*.txt \
         r76_deployment_active_gate_*.txt \
         r77_deployment_trigger_gate_*.txt
do
    [ -f "$f" ] || continue

    echo "--- $f ---"
    grep -Ei \
      '^(VERDICT|RESULT|STATUS|WORKFLOW_COUNT|DEPLOY_TRIGGER_REFERENCES|SAFETY|SECRETS)=' \
      "$f" 2>/dev/null || true
done

echo
echo "============================================================"
echo "END"
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"
echo "============================================================"

} | tee "$OUT"
