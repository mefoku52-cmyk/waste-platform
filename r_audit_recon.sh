#!/data/data/com.termux/files/usr/bin/bash
set -u

echo "===== PROJECT ====="
pwd
echo

echo "===== R AUDIT SCRIPTS ====="
find . -maxdepth 3 -type f \
  \( -name 'phase_p0_*_r*.sh' -o -name 'r[0-9]*_*.sh' \) \
  -not -path './.git/*' \
  -not -path './.closure_truth/*' \
  -print | sort
echo

echo "===== R RESULT FILES ====="
find . -maxdepth 3 -type f -name '*.txt' \
  -not -path './.git/*' \
  -not -path './.closure_truth/*' \
  -not -name '*_all_text.txt' \
  -not -name 'GLOBAL_*' \
  -not -name '*TRUTH_MAP*' \
  -not -name '*DECISION_MAP*' \
  -not -name '*META_AUDIT*' \
  -not -name '*FRONTIER*' \
  -not -name 'r*_files.txt' \
  -not -name 'r*_reports.txt' \
  -not -name 'r*_signals.txt' \
  -not -name 'r*_status_lines.txt' \
  -print | sort
echo

echo "===== EXACT R IDENTITIES ====="
find . -maxdepth 3 -type f \
  -not -path './.git/*' \
  -not -path './.closure_truth/*' \
  -print \
  | sed -nE 's#.*(P0_[0-9]+_R[0-9]+).*#\1#p' \
  | sort -u
echo

echo "===== RESULT / VERDICT / STATUS ====="
grep -RInE \
  '^[[:space:]]*(RESULT|VERDICT|STATUS|COMPLIANCE|FINAL_VERDICT|SAFETY|SECRETS)[[:space:]]*=' \
  --include='*.sh' \
  --include='*.txt' \
  . \
  --exclude-dir=.git \
  --exclude-dir=.closure_truth \
  --exclude='*_all_text.txt' \
  --exclude='GLOBAL_*' \
  --exclude='*TRUTH_MAP*' \
  --exclude='*DECISION_MAP*' \
  --exclude='*META_AUDIT*' \
  --exclude='*FRONTIER*' \
  --exclude='r*_files.txt' \
  --exclude='r*_reports.txt' \
  --exclude='r*_signals.txt' \
  --exclude='r*_status_lines.txt' \
  2>/dev/null | sort
echo

echo "===== AUDIT INTENT / REQUIREMENT SIGNALS ====="
grep -RInE \
  'PURPOSE|REQUIREMENT|EXPECTED|ASSERT|CHECK|ACCEPTANCE|MUST|SHOULD|BLOCKER|CLOSURE|AUTHORITY|PROOF' \
  --include='phase_p0_*_r*.sh' \
  --include='r[0-9]*_*.sh' \
  . 2>/dev/null | sort
echo

echo "===== R42-R56 ====="
for f in $(find . -maxdepth 3 -type f -name '*.sh' \
    -not -path './.git/*' \
    -not -path './.closure_truth/*' | sort); do

    case "$f" in
        *r42*|*r43*|*r44*|*r45*|*r46*|*r47*|*r48*|*r49*|*r50*|*r51*|*r52*|*r53*|*r54*|*r55*|*r56*)
            echo "--- $f"
            grep -nE \
              'RESULT=|VERDICT=|STATUS=|PURPOSE|REQUIREMENT|EXPECTED|CHECK|ASSERT|FAIL|PASS|BLOCK' \
              "$f" 2>/dev/null
            ;;
    esac
done
echo

echo "===== DEPLOYMENT FILES ====="
for f in \
  docs/deployment.md \
  scripts/deploy.sh \
  docker-compose.yml \
  release.env.example \
  r73_deployment_identity_forensic.sh \
  r74_actual_deployment_identity_sources.sh \
  r75_deployment_identity_decision.sh \
  r76_deployment_active_gate.sh \
  r75_deployment_identity_20260905_111008.txt \
  r76_deployment_active_gate_20260905_111209.txt
do
  if [ -f "$f" ]; then
    echo
    echo "===== FILE: $f ====="
    nl -ba "$f" | sed -n '1,260p'
  fi
done
echo

echo "===== WORKFLOWS ====="
if [ -d .github/workflows ]; then
  find .github/workflows -maxdepth 1 -type f -print
  for f in .github/workflows/*; do
    [ -f "$f" ] || continue
    echo "--- $f"
    nl -ba "$f" | sed -n '1,260p'
  done
else
  echo "NO .github/workflows DIRECTORY"
fi
echo

echo "===== GIT STATUS ====="
git status --short 2>/dev/null || true
echo

echo "===== SAFETY ====="
echo "SAFETY=READ_ONLY"
echo "SECRETS=NOT_PRINTED"
