#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/audit/termux-baseline"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$OUT/quick-audit-$STAMP.txt"

mkdir -p "$OUT"

{
  echo "WASTE-PLATFORM QUICK AUDIT"
  echo "Generated: $(date -Is)"
  echo "Project: $ROOT"
  echo

  echo "== Git status =="
  git -C "$ROOT" status --short --branch 2>&1 || true
  echo

  echo "== Last commit =="
  git -C "$ROOT" log -1 --oneline 2>&1 || true
  echo

  echo "== Installed tools =="
  for cmd in python git node npm rg shellcheck shfmt yamllint actionlint hadolint jq; do
    if command -v "$cmd" >/dev/null 2>&1; then
      printf 'OK   %-12s %s
' "$cmd" "$(command -v "$cmd")"
    else
      printf 'MISS %-12s
' "$cmd"
    fi
  done
  echo

  echo "== Python syntax: src, tests, apps =="
  py_total=0
  py_fail=0
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    py_total=$((py_total + 1))
    if ! python -m py_compile "$file" >/dev/null 2>&1; then
      py_fail=$((py_fail + 1))
      echo "FAIL $file"
    fi
  done < <(
    find "$ROOT/src" "$ROOT/tests" "$ROOT/apps" \
      -type f -name '*.py' \
      -not -path '*/.venv/*' \
      -not -path '*/venv/*' \
      -not -path '*/__pycache__/*' \
      2>/dev/null | sort
  )
  echo "Python files checked: $py_total"
  echo "Python syntax failures: $py_fail"
  echo

  echo "== Shell scripts =="
  sh_total=0
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    sh_total=$((sh_total + 1))
    echo "$file"
  done < <(
    find "$ROOT" -type f -name '*.sh' \
      -not -path '*/.git/*' \
      -not -path '*/.venv/*' \
      -not -path '*/venv/*' \
      -not -path '*/node_modules/*' \
      -not -path '*/audit/*' \
      -not -path '*/reports/*' \
      -not -path '*/audit-output/*' \
      -not -path '*/archived/*' \
      -not -path '*/backups/*' \
      2>/dev/null | sort
  )
  echo "Shell scripts found: $sh_total"
  echo

  echo "== YAML files =="
  find "$ROOT" -type f \
    ( -name '*.yml' -o -name '*.yaml' ) \
    -not -path '*/.git/*' \
    -not -path '*/.venv/*' \
    -not -path '*/venv/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/audit/*' \
    -not -path '*/reports/*' \
    -not -path '*/audit-output/*' \
    -not -path '*/archived/*' \
    -not -path '*/backups/*' \
    2>/dev/null | sort
  echo

  echo "== package.json scripts: read-only =="
  while IFS= read -r package_file; do
    [ -n "$package_file" ] || continue
    echo "--- $package_file ---"
    node -e '
      const fs = require("fs");
      const p = process.argv[1];
      try {
        const d = JSON.parse(fs.readFileSync(p, "utf8"));
        console.log("name:", d.name || "(unnamed)");
        const s = d.scripts || {};
        const keys = Object.keys(s);
        console.log(keys.length ? keys.map(k => "script " + k + ": " + s[k]).join("
") : "scripts: none");
      } catch (e) {
        console.log("FAIL:", e.message);
      }
    ' "$package_file"
  done < <(
    find "$ROOT/apps" -type f -name 'package.json' \
      -not -path '*/node_modules/*' \
      2>/dev/null | sort
  )
  echo

  echo "== TODO/FIXME/not implemented: source only =="
  if command -v rg >/dev/null 2>&1; then
    rg -n \
      --glob '*.py' \
      --glob '*.js' \
      --glob '*.jsx' \
      --glob '*.ts' \
      --glob '*.tsx' \
      --glob '!**/.venv/**' \
      --glob '!**/venv/**' \
      --glob '!**/node_modules/**' \
      '(TODO|FIXME|NotImplementedError|raise NotImplemented)' \
      "$ROOT/src" "$ROOT/apps" "$ROOT/tests" 2>/dev/null | head -300 || true
  else
    echo "SKIP: ripgrep (rg) is not installed."
  fi
  echo

  echo "== Sensitive paths deliberately excluded =="
  echo ".env, .env.*, dump.rdb, .git, .venv, node_modules, audit, reports, backups, archived"
  echo
  echo "END OF REPORT"
} > "$REPORT" 2>&1

printf '%s
' "$REPORT" > "$OUT/latest-path.txt"
echo "REPORT=$REPORT"
