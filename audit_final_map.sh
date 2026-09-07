#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_final_map_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "FINAL AUDIT MAP"
echo "P0/P* + R1-R75 + T1-T75"
echo "TIME=$(date -Is)"
echo "============================================================"

echo
echo "=== P0 / P* FINAL SIGNALS ==="

find . -maxdepth 3 -type f \
  \( -iname 'p*.txt' -o -iname 'p*.sh' \) \
  -not -path './.git/*' \
  -not -iname '*all_text*' \
  -not -iname '*closure_truth*' \
  -not -iname '*frontier*' \
  -not -iname '*history*' \
  -print0 2>/dev/null |
while IFS= read -r -d '' f; do
    R=$(grep -hEi \
      '^(RESULT|VERDICT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
      "$f" 2>/dev/null |
      tail -1)

    [ -n "$R" ] && printf '%s -> %s\n' "$(basename "$f")" "$R"
done

echo
echo "=== R1-R75 FINAL SIGNALS ==="

for n in $(seq 1 75); do
    FOUND=0

    find . -maxdepth 3 -type f \
      \( -iname "r${n}_*.txt" -o -iname "r${n}_*.sh" \
         -o -iname "r${n}-*.txt" -o -iname "r${n}-*.sh" \) \
      -not -path './.git/*' \
      -not -iname '*all_text*' \
      -print0 2>/dev/null |
    while IFS= read -r -d '' f; do
        R=$(grep -hEi \
          '^(VERDICT|RESULT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
          "$f" 2>/dev/null |
          tail -1)

        if [ -n "$R" ]; then
            printf 'R%-2s | %s | %s\n' "$n" "$(basename "$f")" "$R"
        fi
    done
done

echo
echo "=== T1-T75 SIGNAL DISCOVERY ==="

grep -RniE \
  --exclude-dir=.git \
  --exclude='audit_final_map*' \
  --exclude='r*.txt' \
  --exclude='*.log' \
  '(^|[^A-Z])T([1-9]|[1-6][0-9]|7[0-5])([[:space:]_-]|:|=)' \
  . 2>/dev/null |
grep -Ei \
  'VERDICT|RESULT|STATUS|FINAL|T[0-9]+' |
head -100

echo
echo "=== KEY CURRENT DEPLOYMENT SIGNALS ==="

for f in \
    r75_deployment_identity_*.txt \
    r76_deployment_active_gate_*.txt \
    r77_deployment_trigger_gate_*.txt
do
    [ -f "$f" ] || continue
    echo "--- $f ---"
    grep -Ei \
      '^(VERDICT|RESULT|STATUS|WORKFLOW_COUNT|DEPLOY_TRIGGER_REFERENCES|SAFETY|SECRETS)=' \
      "$f" 2>/dev/null
done

echo
echo "=== COUNTS ==="

echo "P_FILES=$(find . -maxdepth 3 -type f \( -iname 'p*.txt' -o -iname 'p*.sh' \) -not -path './.git/*' | wc -l)"
echo "R_FILES=$(find . -maxdepth 3 -type f \( -iname 'r*.txt' -o -iname 'r*.sh' \) -not -path './.git/*' | wc -l)"
echo "T_NAMED_FILES=$(find . -maxdepth 3 -type f \( -iname 't*.txt' -o -iname 't*.sh' \) -not -path './.git/*' | wc -l)"

echo
echo "============================================================"
echo "END"
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"
echo "============================================================"

} | tee "$OUT"
