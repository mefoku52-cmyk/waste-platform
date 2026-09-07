#!/data/data/com.termux/files/usr/bin/bash
set -u

OUT="audit_result_summary_$(date +%Y%m%d_%H%M%S).txt"

{
echo "============================================================"
echo "AUDIT RESULT SUMMARY"
echo "ROOT=."
echo "TIME=$(date -Is)"
echo "============================================================"

echo
echo "=== P / P0-P* AUDITS ==="

find . -maxdepth 3 -type f \
  \( -iname 'p*.sh' -o -iname 'p*.txt' \) \
  -not -path './.git/*' \
  -print0 2>/dev/null |
sort -z |
while IFS= read -r -d '' f; do
    NAME=$(basename "$f")
    RESULT=$(grep -hEi \
      '^(VERDICT|RESULT|STATUS|DECISION|PASS|FAIL|EXIT_CODE|FINAL|STATE|P[0-9]+[[:space:]_-]*(VERDICT|RESULT|STATUS|DECISION))=' \
      "$f" 2>/dev/null |
      tail -3 |
      tr '\n' ';' |
      sed 's/;$//')

    [ -n "$RESULT" ] && echo "$NAME -> $RESULT"
done

echo
echo "=== R1-R75 AUDITS ==="

find . -maxdepth 3 -type f \
  \( -iname 'r*.sh' -o -iname 'r*.txt' \) \
  -not -path './.git/*' \
  -print0 2>/dev/null |
sort -z |
while IFS= read -r -d '' f; do
    NAME=$(basename "$f")

    NUM=$(printf '%s\n' "$NAME" |
      sed -nE 's/^[Rr]([0-9]+).*/\1/p')

    [ -z "$NUM" ] && continue
    [ "$NUM" -gt 75 ] 2>/dev/null && continue

    RESULT=$(grep -hEi \
      '^(VERDICT|RESULT|STATUS|DECISION|PASS|FAIL|EXIT_CODE|FINAL|STATE|R[0-9]+[[:space:]_-]*(VERDICT|RESULT|STATUS|DECISION))=' \
      "$f" 2>/dev/null |
      tail -3 |
      tr '\n' ';' |
      sed 's/;$//')

    [ -n "$RESULT" ] && echo "R$NUM | $NAME -> $RESULT"
done

echo
echo "=== T1-T75 AUDITS ==="

find . -maxdepth 3 -type f \
  \( -iname 't*.sh' -o -iname 't*.txt' \) \
  -not -path './.git/*' \
  -print0 2>/dev/null |
sort -z |
while IFS= read -r -d '' f; do
    NAME=$(basename "$f")

    NUM=$(printf '%s\n' "$NAME" |
      sed -nE 's/^[Tt]([0-9]+).*/\1/p')

    [ -z "$NUM" ] && continue
    [ "$NUM" -gt 75 ] 2>/dev/null && continue

    RESULT=$(grep -hEi \
      '^(VERDICT|RESULT|STATUS|DECISION|PASS|FAIL|EXIT_CODE|FINAL|STATE|T[0-9]+[[:space:]_-]*(VERDICT|RESULT|STATUS|DECISION))=' \
      "$f" 2>/dev/null |
      tail -3 |
      tr '\n' ';' |
      sed 's/;$//')

    [ -n "$RESULT" ] && echo "T$NUM | $NAME -> $RESULT"
done

echo
echo "=== COUNTS ==="

P=$(find . -maxdepth 3 -type f \
  \( -iname 'p*.sh' -o -iname 'p*.txt' \) \
  -not -path './.git/*' 2>/dev/null | wc -l)

R=$(find . -maxdepth 3 -type f \
  \( -iname 'r*.sh' -o -iname 'r*.txt' \) \
  -not -path './.git/*' 2>/dev/null |
  while read -r f; do
    n=$(basename "$f" | sed -nE 's/^[Rr]([0-9]+).*/\1/p')
    [ -n "$n" ] && [ "$n" -le 75 ] && echo "$f"
  done | wc -l)

T=$(find . -maxdepth 3 -type f \
  \( -iname 't*.sh' -o -iname 't*.txt' \) \
  -not -path './.git/*' 2>/dev/null |
  while read -r f; do
    n=$(basename "$f" | sed -nE 's/^[Tt]([0-9]+).*/\1/p')
    [ -n "$n" ] && [ "$n" -le 75 ] && echo "$f"
  done | wc -l)

echo "P_FILES=$P"
echo "R_FILES=$R"
echo "T_FILES=$T"

echo
echo "=== END ==="
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
echo "REPORT=$OUT"

} | tee "$OUT"
