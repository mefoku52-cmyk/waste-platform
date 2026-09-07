#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_clean_summary_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "CLEAN AUDIT RESULT SUMMARY"
echo "P0/P* | R1-R75 | T1-T75"
echo "TIME=$(date -Is)"
echo "============================================================"

echo
echo "=== P0 / P* ==="

find . -maxdepth 2 -type f \
  \( -iname 'p*.txt' -o -iname 'P*.txt' \) \
  -not -iname '*all_text*' \
  -not -iname '*closure_truth*' \
  -not -iname '*frontier*' \
  -print0 2>/dev/null |
while IFS= read -r -d '' f; do
    R=$(grep -hEi \
      '^(RESULT|VERDICT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
      "$f" 2>/dev/null | tail -1)

    [ -n "$R" ] && printf '%s -> %s\n' "$(basename "$f")" "$R"
done

echo
echo "=== R1-R75 ==="

for n in $(seq 1 75); do
    found=0

    while IFS= read -r -d '' f; do
        R=$(grep -hEi \
          '^(VERDICT|RESULT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
          "$f" 2>/dev/null | tail -1)

        if [ -n "$R" ]; then
            printf 'R%-2s | %s -> %s\n' "$n" "$(basename "$f")" "$R"
            found=1
        fi
    done < <(
        find . -maxdepth 2 -type f \
          \( -iname "r${n}_*.txt" -o -iname "r${n}-*.txt" \
             -o -iname "R${n}_*.txt" -o -iname "R${n}-*.txt" \) \
          -not -iname '*all_text*' \
          -print0 2>/dev/null
    )
done

echo
echo "=== T1-T75 ==="

for n in $(seq 1 75); do
    while IFS= read -r -d '' f; do
        R=$(grep -hEi \
          '^(VERDICT|RESULT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
          "$f" 2>/dev/null | tail -1)

        [ -n "$R" ] &&
            printf 'T%-2s | %s -> %s\n' "$n" "$(basename "$f")" "$R"
    done < <(
        find . -maxdepth 2 -type f \
          \( -iname "t${n}_*.txt" -o -iname "t${n}-*.txt" \
             -o -iname "T${n}_*.txt" -o -iname "T${n}-*.txt" \) \
          -not -iname '*all_text*' \
          -print0 2>/dev/null
    )
done

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
      "$f" 2>/dev/null
done

echo
echo "============================================================"
echo "END"
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"
echo "============================================================"

} | tee "$OUT"
