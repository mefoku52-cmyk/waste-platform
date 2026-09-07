#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_r_final_resolver_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "FINAL R AUDIT RESULT RESOLVER"
echo "R1-R76"
echo "TIME=$(date -Is)"
echo "============================================================"

TMP=$(mktemp)

find . -type f -name '*.txt' \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './vendor/*' \
  -not -path './build/*' \
  -not -path './dist/*' \
  -not -name '*_all_text*' \
  -not -name '*closure_truth*' \
  -not -name '*frontier*' \
  -not -name 'r*_files.txt' \
  -not -name 'r*_reports.txt' \
  -not -name 'r*_signals.txt' \
  -not -name 'r*_status_lines.txt' \
  -print 2>/dev/null |
while IFS= read -r f; do

    base=$(basename "$f")

    # Presné R číslo iba z prefixu p0..._rNN_ alebo rNN_
    r=$(printf '%s\n' "$base" |
      grep -oEi '^p0[-_][0-9]+[-_]r[0-9]+[-_]|^r[0-9]+[-_]' |
      grep -oEi 'r[0-9]+' |
      head -1 |
      tr '[:lower:]' '[:upper:]' || true)

    [ -n "$r" ] || continue

    result=$(grep -hEi \
      '^[[:space:]]*(RESULT|VERDICT|FINAL_RESULT|FINAL_VERDICT|STATUS)=' \
      "$f" 2>/dev/null |
      tail -1 || true)

    [ -n "$result" ] || continue

    printf '%s\t%s\t%s\n' "$r" "$base" "$result"

done > "$TMP"

echo
echo "=== FINAL R MAP ==="

for n in $(seq 1 76); do

    r="R$n"

    matches=$(awk -F '\t' -v r="$r" '$1==r {print}' "$TMP")

    if [ -z "$matches" ]; then
        printf "%-4s | MISSING\n" "$r"
        continue
    fi

    # R75/R76: aktuálny samostatný deployment report má prioritu
    if [ "$n" -ge 75 ]; then
        printf '%s\n' "$matches" |
        tail -1 |
        awk -F '\t' '{printf "%-4s | %-70s | %s\n",$1,$2,$3}'
        continue
    fi

    # Ak je viac reportov, zobraz všetky, ale iba výsledkové txt
    printf '%s\n' "$matches" |
    awk -F '\t' '{printf "%-4s | %-70s | %s\n",$1,$2,$3}'

done

echo
echo "=== CONFIRMED R IDS ==="

awk -F '\t' '{print $1}' "$TMP" |
sort -Vu |
tr '\n' ' '
echo

echo
echo "=== MISSING R IDS ==="

for n in $(seq 1 76); do
    r="R$n"
    if ! awk -F '\t' -v r="$r" '$1==r {found=1} END{exit !found}' "$TMP"; then
        printf "%s " "$r"
    fi
done
echo

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
