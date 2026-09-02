#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

cd "$HOME/waste-platform"

echo "== tracked paths under __triage_archive =="
git ls-files '__triage_archive/*' | sed -n '1,80p'
echo

echo "== status before =="
git status --short | sed -n '1,120p'
echo

if git ls-files --error-unmatch __triage_archive >/dev/null 2>&1; then
  echo "Top-level __triage_archive entry is tracked."
else
  echo "Top-level __triage_archive entry itself not tracked; removing tracked children by pathspec."
fi

if git ls-files '__triage_archive/*' | grep -q .; then
  if [ -e "__triage_archive" ]; then
    git rm -r --cached __triage_archive
  else
    git rm -r __triage_archive 2>/dev/null || true
    git add -u __triage_archive
  fi
fi

if git ls-files '_local_archive/*' | grep -q .; then
  if [ -e "_local_archive" ]; then
    git rm -r --cached _local_archive
  else
    git rm -r _local_archive 2>/dev/null || true
    git add -u _local_archive
  fi
fi

echo
echo "== status after cleanup staging =="
git status --short | sed -n '1,160p'
echo

git add .gitignore

git diff --cached --check
git diff --cached --stat

git commit -m "chore: remove local archive artifacts from version control"
